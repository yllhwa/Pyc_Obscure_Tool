import xdis
import marshal
import types
import struct
import opcode
import math
import random
# import dill

def pack32(n):
    return struct.pack("<I", n)

def pack16(n):
    return struct.pack("<H", n)
class Obscure:
    def __init__(self, filename=None):
        self.float_version  : float
        self.magic_int      : int
        self.timestamp      : int
        self.co             : types.CodeType
        self.ispypy         : bool
        self.source_size    : int
        self.sip_hash       : int
        self.instr_offset   : list

        if filename is not None:
            self.load_pyc(filename)
    def _load_pyc(self, filename):
        return xdis.load_module(filename)

    def load_pyc(self, filename):
        (
            self.float_version,
            self.timestamp,
            self.magic_int,
            self.co,
            self.ispypy,
            self.source_size,
            self.sip_hash,
        ) = self._load_pyc(filename)
    def new_code_object(self,
                        argcount       = None,
                        kwonlyargcount = None,
                        nlocals        = None,
                        stacksize      = None,
                        flags          = None,
                        code           = None,
                        consts         = None,
                        names          = None,
                        varnames       = None,
                        filename       = None,
                        name           = None,
                        firstlineno    = None,
                        lnotab         = None,
                        freevars       = None,
                        cellvars       = None,
                        ):
        if argcount is None:
            argcount = self.co.co_argcount
        if kwonlyargcount is None:
            kwonlyargcount = self.co.co_kwonlyargcount
        if nlocals is None:
            nlocals = self.co.co_nlocals
        if stacksize is None:
            stacksize = self.co.co_stacksize
        if flags is None:
            flags = self.co.co_flags
        if code is None:
            code = self.co.co_code
        if consts is None:
            consts = self.co.co_consts
        if names is None:
            names = self.co.co_names
        if varnames is None:
            varnames = self.co.co_varnames
        if filename is None:
            filename = self.co.co_filename
        if name is None:
            name = self.co.co_name
        if firstlineno is None:
            firstlineno = self.co.co_firstlineno
        if lnotab is None:
            lnotab = self.co.co_lnotab
        if freevars is None:
            freevars = self.co.co_freevars
        if cellvars is None:
            cellvars = self.co.co_cellvars

        return types.CodeType(
            argcount,
            kwonlyargcount,
            nlocals,
            stacksize,
            flags,
            code,
            tuple(consts),
            tuple(names),
            tuple(varnames),
            filename,
            name,
            firstlineno,
            lnotab,
            tuple(freevars),
            tuple(cellvars),
        )
    def write_pyc(self, filename):
        s = pack16(self.magic_int) + b"\r\n"
        s += pack32(0) + pack32(self.timestamp) + pack32(self.source_size)
        s += marshal.dumps(self.co)
        with open(filename, 'wb') as fw:
            fw.write(s)

    def modify_filename(self, modified_filename):
        self.co = self.new_code_object(filename=modified_filename)
    
    def my_obscure(self):
        code = self.co.co_code
        tag = 0
        code_map = []
        for index in range(0,len(code),2):
            operator = code[index:index+1]
            operand = code[index+1:index+2]
            p_code = {
                "operator":opcode.opname[int.from_bytes(operator,byteorder="little")],
                "operand":int.from_bytes(operand,byteorder="little"),
                "tag":tag,
                "jump_tag":0
            }
            if p_code["operator"]=="JUMP_FORWARD":
                p_code["operator"]="JUMP_ABSOLUTE"
                p_code["jump_tag"]=int(p_code["tag"]+(p_code["operand"]+2)/2)
            elif p_code["operator"]=="JUMP_IF_FALSE_OR_POP" or p_code["operator"]=="JUMP_IF_TRUE_OR_POP" or p_code["operator"]=="POP_JUMP_IF_FALSE" or p_code["operator"]=="POP_JUMP_IF_TRUE" or p_code["operator"]=="JUMP_ABSOLUTE":
                p_code["jump_tag"]=int(p_code["operand"]/2)
            tag+=1
            code_map.append(p_code)
        # 分为n等份
        n = 8
        length = len(code_map)
        code_map_split = []
        for i in range(n):
            one_list = code_map[math.floor(i / n * length):math.floor((i + 1) / n * length)]
            if i!=n-1:
                p_code = {
                    "operator":"JUMP_ABSOLUTE",
                    "operand":233,
                    "tag":tag,
                    "jump_tag":code_map[math.floor((i + 1) / n * length)].get("tag")
                }
                tag+=1
                one_list.append(p_code)
            code_map_split.append(one_list)
        # 除了第一块全部打乱
        code_map_random = code_map_split[1:]
        code_map_split = code_map_split[:1]
        random.shuffle(code_map_random)
        code_map_split.extend(code_map_random)
        output_list = []
        for i in code_map_split:
            for j in i:
                output_list.append(j)
        for index1, op in enumerate(output_list):
            if "JUMP" in op["operator"]:
                des_tag = op["jump_tag"]
                for index2, opp in enumerate(output_list):
                    if opp.get("tag")==des_tag:
                        output_list[index1]["operand"]=index2*2
                        break
        output_list_byte = []
        for op in output_list:
            output_list_byte.append(opcode.opmap[op["operator"]])
            output_list_byte.append(op["operand"])
        _bytes = bytes(output_list_byte)
        self.co = self.new_code_object(code=_bytes)
file = input("输入需要混淆的pyc文件名/路径:")
obs = Obscure(file)
obs.my_obscure()
obs.write_pyc(input("输入输出的pyc文件名/路径:"))