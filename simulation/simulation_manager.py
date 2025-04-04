import os
import json
from datetime import datetime

import opendssdirect as dss

from opendss_powerflow_service.models.result import PfResult, PfResultNode, PfResultLine


class SimulationManager:

    dir = './tmp/'
    model_dir = './tmp/models/'
    simulation_params = None
    circuit_id = None
    nominal_voltages = None

    def __init__(self, circuit_id, simulation_params: dict):
        self.dss = dss
        self.circuit_id = circuit_id
        if isinstance(simulation_params, str):
            self.simulation_params = json.loads(simulation_params)
        else:
            self.simulation_params = simulation_params

    def load_circuit_model(self, circuit_id, circuit_model):
        self.dss.Text.Command('clear')
        for i in circuit_model.sources:
            dss_string = f"New circuit.{circuit_id} bus1={i.bus1} pu={i.pu} basekv={i.basekv} r1={i.r1} x1={i.x1} r0={i.r1} x0={i.x1}"
            self.dss.Text.Command(dss_string)
            break
        for i in circuit_model.linecodes:
            dss_string = f"New Linecode.{i.name} units={i.units} nphases={i.nphases} Faultrate={i.faultrate} Rmatrix=({i.rmatrix}) Xmatrix=({i.xmatrix}) Cmatrix=({i.cmatrix}) normamps={i.normamps}"
            self.dss.Text.Command(dss_string)
        for i in circuit_model.lines:
            dss_string = f"New Line.{i.name} units={i.units} Length={i.length} bus1={i.bus1} bus2={i.bus2} switch={i.switch} enabled={i.enabled} phases={i.phases} Linecode={i.linecode}"
            self.dss.Text.Command(dss_string)
        for i in circuit_model.transformers:
            dss_string = f"New Transformer.{i.name} phases={i.phases} windings=2 wdg=1 conn=delta Kv={i.kv_primary} kva={i.kva} bus={i.bus_primary} wdg=2 conn=delta Kv={i.kv_secondary} kva={i.kva} bus={i.bus_secondary}"
            self.dss.Text.Command(dss_string)
        for i in circuit_model.capacitors:
            dss_string = f"New Capacitor.{i.name} bus1={i.bus} Kv={i.kv} Kvar={i.kvar} conn={i.conn} phases={i.phases}"
            self.dss.Text.Command(dss_string)
        for i in circuit_model.loads:
            dss_string = f"New Load.{i.name} conn={i.conn} bus1={i.bus} kV={i.kv} kW={i.kw} kvar={i.kvar} Phases={i.phases}"
            self.dss.Text.Command(dss_string)

    def save_circuit_model_to_disk(self):
        tmp_model_dir = os.path.join(self.model_dir, self.circuit_id)
        if not os.path.exists(tmp_model_dir):
            os.makedirs(tmp_model_dir)
        print(f"Saving circuit model to {tmp_model_dir}")
        self.dss.Text.Command(f'save circuit dir="{tmp_model_dir}"')

    def export_data(self, export_type='capacity'):
         self.dss.Text.Command(f'export {export_type}')

    def load_file(self, path=None):
        if path is None:
            path = self.simulation_params['modelpath']
        self.dssFileName = path
        self.dss.Text.Command('Redirect "' +path+'"')

    def set_load(self, scaling_factor=None):
        tot = 0.0
        dss.Loads.First()
        while True:
            dss.Circuit.SetActiveElement(dss.Loads.Name())
            if scaling_factor is not None:
                new_kw = dss.Loads.kW() * 2
                dss.Loads.kW(new_kw)
                tot += new_kw
            if not dss.Loads.Next() > 0:
                break
        print(f"Total load after scaling: {tot} kW")

    def create_pf_result(self):
        return {
            "circuit": self.circuit_id,
            "run_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "converged": self.dss.Solution.Converged(),
            "total_kw": dss.Circuit.TotalPower()[0],
            "total_kvar": dss.Circuit.TotalPower()[1],
            "process_time": self.dss.Solution.ProcessTime(),
            "total_time": self.dss.Solution.TotalTime(),
            "total_iterations": self.dss.Solution.TotalIterations(),
            'control_iterations': self.dss.Solution.ControlIterations(),
            'algorithm': self.dss.Solution.Algorithm(),
            'control_mode': self.dss.Solution.ControlMode(),
            'convergence': self.dss.Solution.Convergence(),
            'mode': self.dss.Solution.Mode()
            }
        
    def run_powerflow(self, scaling_factor=None):
        if scaling_factor: 
            self.set_load(scaling_factor=scaling_factor)
        self.dss.run_command("solve")
        self.get_nomina_voltages()
        return self.create_pf_result()
    
    def get_nomina_voltages(self):
        self.nominal_voltages = {}
        dss.Loads.First()
        while True:
            if dss.Loads.kV() and dss.Loads.kV() > 0:
                self.nominal_voltages['Load.'+dss.Loads.Name()] = dss.Loads.kV()
            if not dss.Loads.Next() > 0:
                break
    
    def get_pce_elements(self):
        dss.Circuit.FirstPCElement()
        while True:
            if dss.ActiveClass.ActiveClassName() == 'Load':
                volt_magnitudes = dss.CktElement.VoltagesMagAng()
                for phase in dss.CktElement.NodeOrder():
                    volta = volt_magnitudes.pop(0) / 1000  # Convert to kV
                    angle = volt_magnitudes.pop(0)
            if not dss.Circuit.NextPCElement() > 0:
                break
    
    def get_bus_results(self):
        buses = dss.Circuit.AllBusNames()
        node_results = []
        for bus in buses:
            nresult = PfResultNode(name=bus, circuit=self.circuit_id)
            volt_magnitudes = dss.Bus.puVmagAngle()[::2]
            for phase in dss.Bus.Nodes():
                if phase == 1:
                    nresult.volta = volt_magnitudes.pop(0)
                elif phase == 2:
                    nresult.voltb = volt_magnitudes.pop(0)
                elif phase == 3:
                    nresult.voltc = volt_magnitudes.pop(0)
                else:
                    print(f"Unexpected phase {phase} found in bus {bus}.")
            node_results.append(nresult)
        return node_results

    def get_line_results(self):
        ret = []
        dss.Lines.First()
        while True:
            dss.Circuit.SetActiveElement(dss.Lines.Name())
            line = PfResultLine(name=dss.Lines.Name(),circuit=self.circuit_id, imax=-10000.0)
            line.normal_rating=dss.CktElement.NormalAmps()
            line.emergency_rating=dss.CktElement.EmergAmps()
            currents_mags_angles = dss.CktElement.CurrentsMagAng()
            powers = dss.CktElement.Powers()
            buses = {}
            for i, bus in enumerate(dss.CktElement.BusNames()):
                buses[bus] = {'kw': 0.0,'kvar': 0.0}
                for phase in range(1,dss.CktElement.NumConductors()+1):
                    mag = currents_mags_angles.pop(0)
                    ang = currents_mags_angles.pop(0)
                    kw = powers.pop(0)
                    kvar = powers.pop(0)
                    line.imax = max(line.imax, mag)
                    buses[bus]['kw'] += kw
                    buses[bus]['kvar'] += kvar
            line.loading_percent= line.imax / dss.CktElement.NormalAmps()
            line.kw = buses[dss.CktElement.BusNames()[0]]['kw']
            line.kvar = buses[dss.CktElement.BusNames()[0]]['kvar']
            ret.append(line)
            if not dss.Lines.Next() > 0:
                break
        return ret