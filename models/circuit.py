from typing import List, Optional
from pydantic import BaseModel, PrivateAttr
from sqlmodel import Field, SQLModel
from operator import attrgetter
from bisect import bisect_left, insort

from opendss_powerflow_service.models.components import Source, Bus, Capacitor, Generator, Line, LineCode, Load, Regulator, Transformer, Cable, Switch


class Circuits(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    circuit: Optional[str] = None
    substation: Optional[str] = None
    url: Optional[str] = None
    test: Optional[str] = None
    filenames: Optional[str] = None
    import_flag: Optional[str] = None

class Circuit(BaseModel):
    fields: Circuits
    transformers: List[Transformer] = []
    lines: Optional[List[Line]] = []
    linecodes: Optional[List[LineCode]] = []
    loads: Optional[List[Load]] = []
    buses: Optional[List[Bus]] = []
    sources: Optional[List[Source]] = []
    capacitors: Optional[List[Capacitor]] = []
    _name_index: Optional[dict] = PrivateAttr(default={})

    def get_models(self):
        models = [Line, Load, Capacitor, Generator,  Load, Regulator, Transformer,
                    ]
        return models
        
    def get_models_w_attrib(self, attribut):
        filtered_models = []
        all_models = self.get_models()
        for model in all_models:
            model_dict = model.model_json_schema()
            if attribut in model_dict['properties']:
                filtered_models.append(model)
        return filtered_models

    def __iter__(self):
        for attr, value in vars(self).items():
            if isinstance(value, list):
                yield from value

    def iter_lines(self):
        for attr, value in vars(self).items():
            if isinstance(value, list) and attr in ['lines', 'cables', 'transformers', 'transformerbanks', 'switches']:
                yield from value

    def iter_nodes(self):
        for attr, value in vars(self).items():
            if isinstance(value, list) and attr in ['servicepoints', 'sources', 'loads', 'capacitors', 'generators']:
                yield from value

    def upsert_component(self, component, sort_by='id'):
        cls_name = component.__class__.__name__.lower()
        existing_c = self.get_component_by_id(cls_name, component.id)
        if existing_c is not None:
            comp_dict = component.model_dump()
            for key in comp_dict:
                new_value = getattr(component, key)
                if new_value is not None and new_value != '' and key not in ('name', 'id'):
                    setattr(existing_c, key, new_value)
        else:
            self.add_component(component, sort_by)

    def add_component(self, component, sort_by='id'):
        for attr, value in vars(self).items():
            if str(component.__class__.__name__).lower() in attr.lower():
                insort(value, component, key=attrgetter(sort_by))
                return True
        raise Exception("Invalid component type: " + str(type(component)))
    
    def get_component_by_name(self, ctype, name):
        for attr, value in vars(self).items():
            if isinstance(value, list):
                if ctype.lower() in attr.lower():
                    i = bisect_left(value, name, key=attrgetter('name'))
                    if i != len(value) and value[i].name == name:
                        return value[i]
                    else:
                        return None
                    
    def get_component_by_id(self, ctype, id):
        for attr, value in vars(self).items():
            if isinstance(value, list):
                if ctype.lower() in attr.lower():
                    i = bisect_left(value, id, key=attrgetter('id'))
                    if i != len(value) and value[i].id == id:
                        return value[i]
                    else:
                        return None
                                 
    def get_component(self, attr, value):
        for component in self:
            if getattr(component, attr) == value:
                return component
        return None
    
    def get_components_w_attribute(self, attr):
        models = self.get_models_w_attrib(attr)
        model_names = [i.__tablename__ for i in models]
        for attr, value in vars(self).items():
            if isinstance(value, list) and attr.rstrip('s') in model_names:
                yield from value

    def describe(self):
        print('fields:' + str(self.fields))
        for attr, value in vars(self).items():
            if isinstance(value, list):
                print(attr + ': ' + str(len(value)))

    def build_asset_relationships(self):
        for wire_position in self.wirepositions:
            wire_position.wireinfo = self.get_component_by_id('wireinfos', wire_position.wireinfoid)
            wire_spacing_info = self.get_component_by_id('wirespacinginfos', wire_position.wirespacinfoId) 
            wire_position.wirespacinfo = wire_spacing_info
            wire_spacing_info.wirepositions.append(wire_position)

        for line in self.lines:
            if line.perlengthsequenceimpendanceid is not None and line.perlengthsequenceimpedance is None:
                line.perlengthsequenceimpedance =  self.get_component_by_id('perlengthsequenceimpendances', line.perlengthsequenceimpendanceid)
                if line.perlengthsequenceimpedance is None:
                    line.perlengthsequenceimpendanceid = None
            if line.wirespacinginfoid is not None and line.wirespacinginfo is None:
                line.wirespacinginfo =  self.get_component_by_id('wirespacinginfos', line.wirespacinginfoid)
                if line.wirespacinginfo is None:
                    line.wirespacinginfoid = None

        for cap_control in self.capacitorcontrols:
            cap_control.capacitr = self.get_component_by_id('capacitors', cap_control.capacitorid)
            if cap_control.capacitr is None:
                cap_control.capacitorid = None

    def build_connectivity_relationships(self):
        # associate connectivity nodes with locations
        for n in self.nodes:
            location_name = n.name.split('.')[0]
            location = self.circuit_model.get_component_by_name('location', location_name)
            if location is not None:
                n.locationId = location.id
                n.location = location
                
        # associate point components with connectivity nodes
        for n in self.iter_nodes():
            if n.terminalId is not None:
                n.terminal = self.get_component_by_id('nodes', n.terminalId)
        # associate line components with connectivity nodes
        for l in self.iter_lines():
            if l.terminalId1 is not None:
                l.terminal1 = self.get_component_by_id('nodes', l.terminalId1)
            if l.terminalId2 is not None:
                l.terminal2 = self.get_component_by_id('nodes', l.terminalId2)

    def from_json(self, json_data):
        for key in json_data:
            if key == 'fields':
                self.fields = Circuits(**json_data[key])
                continue
            elif key == 'transformers':
                for c in json_data[key]:
                    self.transformers.append(Transformer(**c))  
            elif key == 'lines':
                for c in json_data[key]:
                    self.transformers.append(Line(**c))  
            elif key == 'cables':
                for c in json_data[key]:
                    self.transformers.append(Cable(**c))  
            elif key == 'switches':
                for c in json_data[key]:
                    self.transformers.append(Switch(**c))
            else:
                raise Exception("Invalid key in Circuit: " + key)
  
    def to_geojson(self):
        geojson = {
            "type": "FeatureCollection",
            "features": []
            }
        for component in self:
            if component._geojson_feature:
                feature = component.to_geojson()
                if feature is not None:
                    geojson['features'].append(feature)
        return geojson


        

