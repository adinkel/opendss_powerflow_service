import psycopg2
import re
import requests
from urllib.parse import urljoin

# Database connection settings
db_config = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'postgres',
    'user': 'PGUSER',
    'password': 'PGPASSWORD'
}

def connect_db():
    return psycopg2.connect(**db_config)

# Parse OpenDSS content from memory (string) with circuit context
def parse_opendss_text(text, circuit):
    data = {
        'sources': [],
        'buses': set(),
        'lines': [],
        'loads': [],
        'transformers': [],
        'capacitors': [],
        'linecodes': [],
        'xfmrcodes': [],
        'wiredata': [],
        'linespacing': [],
        'capcontrols': []
    }

    for line in text.splitlines():
        line = line.strip()

        if line.lower().startswith('new circuit.'):
            match = re.search(
                r'new circuit\.(\S+)\s+bus1=(\S+)\s+pu=([\d\.]+)\s+basekV=([\d\.]+)\s+R1=([\deE\.\-]+)\s+X1=([\deE\.\-]+)\s+R0=([\deE\.\-]+)\s+X0=([\deE\.\-]+)',
                line, re.I
            )
            if match:
                name, bus1, pu, basekv, r1, x1, r0, x0 = match.groups()
                data['sources'].append((
                    name, bus1, float(pu), float(basekv),
                    float(r1), float(x1), float(r0), float(x0), circuit
                ))


        if line.lower().startswith('new xfmrcode.'):
            match = re.match(r'new xfmrcode\.(\S+)(.*)', line, re.I)
            if match:
                name, params = match.groups()
                xfmrcode_fields = {
                    "name": name,
                    "circuit": circuit,
                    "phases": None,
                    "windings": None,
                    "xhl": None,
                    "noloadloss": None,
                    "imag": None
                }
                params = params.strip()
                xfmrcode_fields.update({k.lower(): v for k, v in re.findall(r'(\w+)=([^\s]+)', params)})
                data['xfmrcodes'].append(tuple(xfmrcode_fields.values()))

        elif any(line.lower().startswith(f"new {prefix}.") for prefix in ["wiredata", "tsdata", "cndata"]):
            match = re.match(r'new (\S+)\.(\S+)\s+(.*)', line, re.I)
            if match:
                category, name, param_str = match.groups()
                parsed = dict(re.findall(r'(\w+)=([^\s]+)', param_str))
                data['wiredata'].append((
                    category, name, circuit,
                    parsed.get('NormAmps'), parsed.get('DIAM'), parsed.get('GMRac'),
                    parsed.get('Rdc'), parsed.get('Rac'), parsed.get('Runits'),
                    parsed.get('Radunits'), parsed.get('gmrunits')
                ))

        elif line.lower().startswith('new linespacing.'):
            match = re.match(r'new linespacing\.(\S+)\s+(.*)', line, re.I)
            if match:
                name, param_str = match.groups()
                parsed = {}
                for key, val in re.findall(r'(\w+)=\[([^\]]+)\]', param_str):
                    parsed[key] = val
                for key, val in re.findall(r'(\w+)=([\w\.-]+)', param_str):
                    if key not in parsed:
                        parsed[key] = val
                parsed['x'] = [float(n) for n in parsed['x'].split()]
                data['linespacing'].append((
                    name, circuit,
                    parsed.get('nconds'), parsed.get('nphases'), parsed.get('units'),
                    parsed.get('x'), parsed.get('h')
                ))

        elif line.lower().startswith('new capcontrol.'):
            match = re.match(r'new capcontrol\.(\S+)\s+(.*)', line, re.I)
            if match:
                name, param_str = match.groups()
                params = dict(re.findall(r'(\b\w+)\s*=\s*([^\s]+)', param_str, re.I))
                data['capcontrols'].append((
                    name, circuit,
                    params.get('capacitor'), params.get('element'),
                    params.get('type'), params.get('vreg'),
                    params.get('band'), params.get('ptratio'),
                    params.get('ctprim')
                ))

        elif line.lower().startswith('new line.'):
            match = re.search(
                r'new line\.(\S+)\s+units=(\w+)\s+length=([\d\.]+)\s+bus1=(\S+)\s+bus2=(\S+)' \
                r'.*?switch=(\w).*?enabled=(\w).*?phases=(\d+).*?linecode=(\S+)',
                line, re.I
            )
            if match:
                name, units, length, bus1, bus2, switch, enabled, phases, linecode = match.groups()
                data['lines'].append((name, bus1, bus2, float(length), units, linecode, switch.lower() == 'y', enabled.lower() == 'y', int(phases), circuit))
                data['buses'].update([(bus1, circuit), (bus2, circuit)])

        elif line.lower().startswith('new load.'):
            match = re.search(
                r'new load\.(\S+)\s+conn=(\w+)\s+bus1=(\S+)\s+kV=([\d\.]+).*?kW=([\d\.]+)\s+kvar=([\d\.]+).*?Phases=(\d+)',
                line, re.I
            )
            if match:
                name, conn, bus, kv, kw, kvar, phases = match.groups()
                data['loads'].append((name, bus, float(kw), float(kvar), float(kv), conn, int(phases), circuit))
                data['buses'].add((bus, circuit))

        elif line.lower().startswith('new transformer.'):
            match = re.search(
                r'new transformer\.(\S+).*?phases=(\d+).*?wdg=1.*?bus=(\S+).*?Kv=([\d\.]+).*?wdg=2.*?bus=(\S+).*?Kv=([\d\.]+).*?kva=([\d\.]+)',
                line, re.I
            )
            if match:
                name, phases, bus_primary, kv_primary, bus_secondary, kv_secondary, kva = match.groups()
                data['transformers'].append((name, bus_primary, bus_secondary, float(kva), float(kv_primary), float(kv_secondary), int(phases), circuit))
                data['buses'].update([(bus_primary, circuit), (bus_secondary, circuit)])

        elif line.lower().startswith('new capacitor.'):
            match = re.search(
                r'new capacitor\.(\S+)\s+bus1=(\S+)\s+phases=(\d+)\s+Kv=([\d\.]+)\s+conn=(\w+)\s+Kvar=([\d\.]+)',
                line, re.I
            )
            if match:
                name, bus, phases, kv, conn, kvar = match.groups()
                data['capacitors'].append((name, bus, float(kv), float(kvar), conn, int(phases), circuit))
                data['buses'].add((bus, circuit))

        elif line.lower().startswith('new linecode.'):
            match = re.search(
                r'new linecode\.(\S+)\s+units=(\w+)\s+nphases=(\d+)\s+Faultrate=([\d\.]+)\s+Rmatrix=\(([^)]+)\)\s+Xmatrix=\(([^)]+)\)\s+Cmatrix=\(([^)]+)\)\s+normamps=([\d\.]+)',
                line, re.I
            )
            if match:
                name, units, nphases, faultrate, rmatrix, xmatrix, cmatrix, normamps = match.groups()
                data['linecodes'].append((name, units, int(nphases), float(faultrate), rmatrix, xmatrix, cmatrix, float(normamps)))

    return data

def merge_data_sets(datasets):
    merged = {
        'sources': [],
        'buses': set(),
        'lines': [],
        'loads': [],
        'transformers': [],
        'capacitors': [],
        'linecodes': [],
        'xfmrcodes': [],
        'wiredata': [],
        'linespacing': [],
        'capcontrols': []
    }
    for ds in datasets:
        for key in merged:
            if key == 'buses':
                merged[key].update(ds[key])
            else:
                merged[key].extend(ds[key])
    return merged

def insert_data(circuit, data):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM source WHERE circuit = %s;", (circuit,))
    cur.execute("DELETE FROM bus WHERE circuit = %s;", (circuit,))
    cur.execute("DELETE FROM line WHERE circuit = %s;", (circuit,))
    cur.execute("DELETE FROM load WHERE circuit = %s;", (circuit,))
    cur.execute("DELETE FROM transformer WHERE circuit = %s;", (circuit,))
    cur.execute("DELETE FROM capacitor WHERE circuit = %s;", (circuit,))

    for src in data['sources']:
        cur.execute("""
            INSERT INTO source (name, bus1, pu, basekv, r1, x1, r0, x0, circuit)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, src)

    for bus, circuit in data['buses']:
        cur.execute("INSERT INTO bus (name, circuit) VALUES (%s, %s);", (bus, circuit))

    for line in data['lines']:
        cur.execute("INSERT INTO line (name, bus1, bus2, length, units, linecode, switch, enabled, phases, circuit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", line)

    for load in data['loads']:
        cur.execute("INSERT INTO load (name, bus, kw, kvar, kv, conn, phases, circuit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", load)

    for transformer in data['transformers']:
        cur.execute("INSERT INTO transformer (name, bus_primary, bus_secondary, kva, kv_primary, kv_secondary, phases, circuit) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", transformer)

    for capacitor in data['capacitors']:
        cur.execute("INSERT INTO capacitor (name, bus, kv, kvar, conn, phases, circuit) VALUES (%s, %s, %s, %s, %s, %s, %s);", capacitor)

    for linecode in data['linecodes']:
        cur.execute("INSERT INTO linecode (name, units, nphases, faultrate, rmatrix, xmatrix, cmatrix, normamps) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);", linecode)

    for x in data['xfmrcodes']:
        try:
            cur.execute("INSERT INTO xfmrcode (name, circuit, phases, windings, xhl, noloadloss, imag) VALUES (%s, %s, %s, %s, %s, %s, %s);", x)
        except TypeError as e:
            print(f"Error inserting xfmrcode {x}: {e}")

    for x in data['wiredata']:
        cur.execute("INSERT INTO wiredata (category, name, circuit, normamps, diam, gmrac, rdc, rac, runits, radunits, gmrunits) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);", x)

    for x in data['linespacing']:
        cur.execute("INSERT INTO linespacing (name, circuit, nconds, nphases, units, x, h) VALUES (%s, %s, %s, %s, %s, %s, %s);", x)

    for x in data['capcontrols']:
        cur.execute("INSERT INTO capcontrol (name, circuit, capacitor, element, type, vreg, band, ptratio, ctprim) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);", x)

    conn.commit()
    cur.close()
    conn.close()

def import_circuit(circuit, s3_path, s3_filenames):

    all_data = []
    for fn in s3_filenames:
        url = urljoin(s3_path, fn)
        print(f"Fetching: {url}")
        response = requests.get(url)
        response.raise_for_status()
        parsed = parse_opendss_text(response.text, circuit)
        all_data.append(parsed)

    merged = merge_data_sets(all_data)
    insert_data(circuit, merged)

