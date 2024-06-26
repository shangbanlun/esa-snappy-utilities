from typing import Union, Optional, List, Tuple, Any
from pathlib import Path
import numpy as np

from esa_snappy import ProductIO
from . import parameter_parser


from colorama import Fore

from datetime import datetime
import xml.etree.ElementTree as ET
import subprocess
from subprocess import run


# * This class serves as a wrapper for the ESA-SNAP (Sentinel Application Platform) Product class,
# * providing a more user-friendly and Pythonic interface for interacting with satellite imagery data.
# * ESA-SNAP is a comprehensive toolbox for the scientific exploitation of Earth Observation missions,
# * especially those of the Sentinel series developed by the European Space Agency (ESA).
class SnapProduct():
    def __init__(self, input: Union[Any, str]) -> None:
        if type(input) == 'org.esa.snap.core.datamodel.Product':
            self.__product = input
        elif isinstance(input, str):
            self.__path = input
            self.__product = ProductIO.readProduct(input)
        else :
            self.__path = str(input)
            self.__product = ProductIO.readProduct(str(input))
            
        self.__product_name = self.__product.getName()
        self.__band_names = list(self.__product.getBandNames())
        self.__band_num = len(self.__band_names)

        self.__height = self.__product.getSceneRasterHeight()
        self.__width = self.__product.getSceneRasterWidth()


    def __del__(self):
        self.__product.closeIO()

    @property
    def product(self):
        return self.__product
    
    @property
    def path(self):
        return self.__path

    @property
    def product_name(self):
        return self.__product_name
    
    @property
    def band_names(self):
        return self.__band_names
    
    @property
    def size(self):
        return self.__height, self.__width

    def __getitem__(self, band_name: str) -> np.ndarray:
        if not isinstance(band_name, str): raise TypeError('The band_name you input must be a string.')
        if band_name not in self.__band_names: raise ValueError(f'The band_name you input must be one of {self.__band_names}.')
        
        band = self.__product.getBand(band_name)
        temp = np.empty((self.__width * self.__height), dtype= np.float32)
        band.readPixels(0, 0, self.__width, self.__height, temp)

        return np.reshape(temp, (self.__height, self.__width))
    
    def __str__(self):
        return f'Product name: {self.__product_name}, resolution: {self.__width}x{self.__height}, bands: {self.__band_names}.'


    def to_numpy(self) -> np.ndarray:
        '''
        return a numpy.ndarray with each band as axis 0, each row as axis 1 and each col as axis 2, namely the shape of ndarray is (band_num x height x width).
        '''
        output = np.empty((self.__band_num, self.__height * self.__width), dtype= np.float64)

        for idx, band_name in enumerate(self.__band_names):
            band = self.__product.getBand(band_name)

            temp = np.empty((self.__width * self.__height), dtype= np.float64)
            band.readPixels(0, 0, self.__width, self.__height, temp)
            output[idx] = temp
            print(f'{idx + 1}/{self.__band_num} band {band_name} completed.')

        return np.reshape(output, (self.__band_num, self.__height, self.__width))
    

    # def write_product(self, path: str, format: Optional[str] = 'BEAM-DIMAP'):
    #     '''
    #     write the product.
    #     '''
    #     print(Fore.BLUE + 'Product writting' + Fore.WHITE + ' for ' + Fore.GREEN + self.product_name + Fore.WHITE + ' starts...')
    #     # ProductIO.writeProduct(self.__product, path, format)
    #     GPF.writeProduct(self.product, File(path), format, False, ProgressMonitor.NULL)
    #     print(Fore.BLUE + 'Product writting' + Fore.WHITE + ' for ' + Fore.GREEN + self.product_name + Fore.WHITE + ' has completed.')
    #     print(Fore.YELLOW + '======================================================================================\n')


# * The classes below is all about using graph process tools (gpt) to complete the process of the SAR images.

from abc import ABC, abstractmethod

class Operator(ABC):
    def __init__(self) -> None:

        self.__operator_name = None
        self.__parameters = None

    @property
    def name(self):
        return self.__operator_name
    
    @property
    def parameters(self):
        return self.__parameters

    @abstractmethod
    def set_parameter():
        pass

    def __call__(self, product: SnapProduct) -> SnapProduct:
        print(Fore.BLUE + self.__operator_name + Fore.WHITE + ' for ' + Fore.GREEN + product.product_name + Fore.WHITE + ' starts ...')

        print(f'gpt {self.__operator_name} -Ssource="{product.path}" -t "{product.path}.dim"')
        
        print(Fore.BLUE + self.__operator_name + Fore.WHITE + ' for ' + Fore.GREEN + product.product_name + Fore.WHITE + ' has completed.')
        print(Fore.YELLOW + '======================================================================================\n')
        return 'Successfully Operation.'

    # * do the operator by the GPF way, i think is not good, i think it's better to use gpt tool in command line.
    # def __call__(self, product: SnapProduct) -> SnapProduct:
    #     print(Fore.BLUE + self.__operator_name + Fore.WHITE + ' for ' + Fore.GREEN + product.product_name + Fore.WHITE + ' starts ...')

    #     print(f'gpt {self.__operator_name} -Ssource="{product.path}" -t "{product.path}.dim"')
        
    #     print(Fore.BLUE + self.__operator_name + Fore.WHITE + ' for ' + Fore.GREEN + product.product_name + Fore.WHITE + ' has completed.')
    #     print(Fore.YELLOW + '======================================================================================\n')
    #     return 'Successfully Operation.'


from .parameter_enum import WriteType

class Read(Operator):
    def __init__(
            self,
            product: SnapProduct,
            is_use_advanced_options: Optional[bool] = False,
            is_copy_metadata: Optional[bool] = True,
        ) -> None:
        super().__init__()

        self._Operator__operator_name = 'Read'
        self._Operator__parameters = {
            'useAdvancedOptions': parameter_parser.boolean_parameter_parser(is_use_advanced_options),
            'file': product.path,
            'copyMetadata': parameter_parser.boolean_parameter_parser(is_copy_metadata),
            'bandNames': None,
            'pixelRegion': f'0,0,{product.size[1]},{product.size[0]}',
            'maskNames': None
        }
    
    def set_parameter():
        pass


class Write(Operator):
    def __init__(
            self,
            output_path: str,
            output_format: WriteType
        ) -> None:
        super().__init__()

        self._Operator__operator_name = 'Write'
        self._Operator__parameters = {
            'file': output_path,
            'formatName': output_format.value
        }
    
    def set_parameter():
        pass

# * functions for writting a graph file which is a xml file.

def _blank_graph_xml():
    root = ET.Element('graph')
    root.set('id', 'Graph')

    version = ET.SubElement(root, 'version')
    version.text = '1.0'

    return root


def _add_dict_into_element(element, dict_: dict):
    for key in dict_:
        sub_element = ET.SubElement(element, key)
        if isinstance(dict_[key], str):    # * for the parameter value is str type.
            sub_element.text = dict_[key]
        elif isinstance(dict_[key], dict):    # * if the parameter value is dict type, keep 
            _add_dict_into_element(sub_element, dict_[key])
        elif dict_[key] == None: continue    # * if the parameter value is none, just skip.


def _add_node(root, node_id: str, operator: Operator, last_node_id: Union[str, List[str], None] = None):
    # * add a node element into root element for input operater.
    node_element = ET.SubElement(root, 'node')
    node_element.set('id', node_id)


    # * add a operater element into node element.
    operator_element = ET.SubElement(node_element, 'operator')
    operator_element.text = operator.name


    # * add a sources element into node element.
    sources_element = ET.SubElement(node_element, 'sources')
    if isinstance(last_node_id, str):
        sourceProduct = ET.SubElement(sources_element, 'sourceProduct')
        sourceProduct.set('refid', last_node_id)
    elif isinstance(last_node_id, list) and all(isinstance(item, str) for item in last_node_id):
        for idx, id in enumerate(last_node_id):
            suffix = f'.{idx}' if idx != 0 else ''
            sourceProduct = ET.SubElement(sources_element, 'sourceProduct' + suffix)
            sourceProduct.set('refid', id)
    elif last_node_id == None:
        pass
    else:
        raise TypeError('The last_node_id should be either a string or a list of strings.')


    # * add a parameters element into node element.
    parameters_element = ET.SubElement(node_element, 'parameters')
    parameters_element.set('class', 'com.bc.ceres.binding.dom.XppDomElement')
    _add_dict_into_element(parameters_element, operator.parameters) 
        
    return root

def _isinstance_by_name(obj, class_name: str):
    return obj.__class__.__name__ == class_name

class Sequential():
    GPT_PATH = 'gpt'
    def __init__(self, *args) -> None:
        # * Get the current date and time.
        home_folder = Path.cwd()
        current_time = datetime.now()
        self.__xml_path = f'{home_folder}/graph_{current_time.date()}-{current_time.hour}-{current_time.minute}-{current_time.second}-{current_time.microsecond}.xml'
        
        self.__gpt_path = self.GPT_PATH
        self.__operators = args    # * store all the operators.


    def process(
            self, 
            input: Union[SnapProduct, Tuple[SnapProduct]], 
            output_path: str, 
            output_format: Optional[WriteType] = WriteType.BEAM_DIMAP,
            log_path: Optional[str] = None
        ) -> None:
        '''
        excuting all the operators by sequence, \n
        if you leave the log_path just the default value(None), the excuting will output the info into terminal real time,
        else the excuting will store the info into the log_path you type in.
        input: SnapProduct or a list of SnapProduct 
        '''


        try:
            output_path = str(output_path)
        except Exception:
            raise TypeError('The output_path you input must be string or can be converted into string by str() function.')
        
        if log_path != None :
            try:
                log_path = str(log_path)
            except Exception:
                raise TypeError('The log_path you input must be string or can be converted into string by str() function.')

        root = _blank_graph_xml()


        # * add all the Read operators as node elements into root. 
        if _isinstance_by_name(input, 'SnapProduct'):    # * for just one product as input.
            root = _add_node(root, 'Read', Read(input))
            last_node_id = 'Read'
        elif isinstance(input, tuple) and all(_isinstance_by_name(item, 'SnapProduct') for item in input):    # * for multiable products as input.
            last_node_id = []
            for idx, p in enumerate(input):
                suffix = f'({idx+1})' if idx != 0 else ''
                node_id = 'Read' + suffix
                root = _add_node(root, node_id, Read(p))
                last_node_id.append(node_id)
        else:
            raise TypeError("The input parameter should be either a SnapProduct instance or a tuple of SnapProduct instances.")


        # * add all the operators as node elements into root.
        operator: Operator
        for operator in self.__operators:
            root = _add_node(root, operator.name, operator, last_node_id)
            last_node_id = operator.name


        # * add the Write operator as node element into root.
        root = _add_node(root, 'Write', Write(output_path, output_format), last_node_id)


        # * save the graph xml file.
        tree = ET.ElementTree(root)
        tree.write(self.__xml_path)

        if log_path != None :

            try:
                # * run the gpt graph xml in file.
                res = run(
                    (self.__gpt_path, self.__xml_path), 
                    stdout= subprocess.PIPE, 
                    stderr= subprocess.PIPE, 
                    text= True,
                    check= True
                )
                stdout = res.stdout
                stderr = res.stderr

            except subprocess.CalledProcessError as e:
                stdout = 'error!\n'
                stderr = e.output
                print('Get error from subprocess.CalledProcessEror..')
            
            except FileNotFoundError as e:
                stdout = 'error!\n'
                stderr = e.strerror
                print('Get error from FileNotFoundError..')

            except Exception as e:
                stdout = 'error!\n'
                stderr = e.output
                print('Get error from Exception..')


            # * save all the output from the terminal.
            with open(log_path, 'w') as f:
                f.write('Output:\n')
                f.write(stdout)
                f.write('ERROR:\n')
                f.write(stderr)
                f.close()
                
        else:
            run((self.__gpt_path, self.__xml_path))


        # * delete the gpt graph xml file and print info. 
        Path(self.__xml_path).unlink()

    
    def __call__(
            self, input: Union[SnapProduct, Tuple[SnapProduct]], 
            output_path: str, 
            output_format: Optional[WriteType] = WriteType.BEAM_DIMAP,
            log_path: Optional[str] = None
        ) -> None:


        self.process(input, output_path, output_format, log_path)