## Delua51 - A Lua 5.1 decompiler, aimed towards compiled lua files with stripped debug information.



### Reader

class Reader:
    def __init__(self, FileName, Endianness = "little"):
        self.Pointer = 0
        self.File = open(FileName, "rb")

        self.SizeT = 4
        self.IntSize = 4
        self.LuaNumberSize = 8
        self.Endianness = Endianness
    
    def ReadByte(self):
        self.Pointer += 1
        return self.File.read(1)
    
    def ReadByteAsInt(self):
        self.Pointer += 1
        return int.from_bytes(self.File.read(1), self.Endianness)
    
    def ReadBytes(self, Amount):
        self.Pointer += Amount
        return self.File.read(Amount)
    
    def ReadInt(self):
        self.Pointer += self.IntSize
        return int.from_bytes(self.File.read(self.IntSize), self.Endianness)

    def ReadSizeT(self):
        self.Pointer += self.SizeT
        return int.from_bytes(self.File.read(self.SizeT), self.Endianness)
    
    def ReadLuaNumber(self):
        self.Pointer += self.LuaNumberSize
        return int.from_bytes(self.File.read(self.LuaNumberSize), self.Endianness)
    
    def ReadString(self):
        Size = self.ReadSizeT()
        String = self.File.read(Size)
        self.Pointer += Size

        return String.decode("utf-8")
    
    def Close(self):
        self.File.close()


### Logger

class Logger: # 0 = None, 1 = Info, 2 = Warning, 3 = Error
    Levels = ["None", "Info", "Warning", "Error"]

    def __init__(self, LogLevel):
        self.LogLevel = LogLevel

    def Send(self, Message, Level):
        if self.LogLevel == 0:
            return
        
        if Level <= self.LogLevel:
            print("[{}] {}".format(self.Levels[Level], Message))
    
    def SetLogLevel(self, LogLevel):
        if LogLevel < 0 or LogLevel > 3:
            self.Send("Invalid LogLevel", 2)
            return

        self.LogLevel = LogLevel


### Mappings

OpCodes = {0:"MOVE", 1:"LOADK", 2:"LOADBOOL", 3:"LOADNIL", 4:"GETUPVAL", 5:"GETGLOBAL", 6:"GETTABLE", 7:"SETGLOBAL", 8:"SETUPVAL", 9:"SETTABLE", 10:"NEWTABLE", 11:"SELF", 12:"ADD", 13:"SUB", 14:"MUL", 15:"DIV", 16:"MOD", 17:"POW", 18:"UNM", 19:"NOT", 20:"LEN", 21:"CONCAT", 22:"JMP", 23:"EQ", 24:"LT", 25:"LE", 26:"TEST", 27:"TESTSET", 28:"CALL", 29:"TAILCALL", 30:"RETURN", 31:"FORLOOP", 32:"FORPREP", 33:"TFORLOOP", 34:"SETLIST", 35:"CLOSE", 36:"CLOSURE", 37:"VARARG"}

OpModes = {"MOVE":"ABC", "LOADK":"ABx", "LOADBOOL":"ABC", "LOADNIL":"ABC", "GETUPVAL":"ABC", "GETGLOBAL":"ABx", "GETTABLE":"ABC", "SETGLOBAL":"ABx", "SETUPVAL":"ABC", "SETTABLE":"ABC", "NEWTABLE":"ABC", "SELF":"ABC", "ADD":"ABC", "SUB":"ABC", "MUL":"ABC", "DIV":"ABC", "MOD":"ABC", "POW":"ABC", "UNM":"ABC", "NOT":"ABC", "LEN":"ABC", "CONCAT":"ABC", "JMP":"sBx", "EQ":"ABC", "LT":"ABC", "LE":"ABC", "TEST":"ABC", "TESTSET":"ABC", "CALL":"ABC", "TAILCALL":"ABC", "RETURN":"ABC", "FORLOOP":"sBx", "FORPREP":"sBx", "TFORLOOP":"ABC", "SETLIST":"ABC", "CLOSE":"ABC", "CLOSURE":"ABx", "VARARG":"ABC"}


### Parser

class Parser:
    def __init__(self, ReaderObject):
        self.Reader = ReaderObject

    def Parse(self):
        self.ParseHeader()
        self.MainProto = self.ParseProto()

    def ParseInstruction(self, Instruction, Proto):
        ParsedInstruction = {}

        OpCode = Instruction & 0x3F
        if OpCode < 0 or OpCode > 37:
            Logger.Send("Invalid OpCode", 3)
            exit()

        ParsedInstruction["OpCode"] = OpCodes[OpCode]

        OpMode = OpModes[ParsedInstruction["OpCode"]]

        if OpMode == "ABC":
            ParsedInstruction["A"] = ((Instruction >> 6) & 0xFF)
            ParsedInstruction["B"] = ((Instruction >> 23) & 0x1FF)
            ParsedInstruction["C"] = ((Instruction >> 14) & 0x1FF)
        elif OpMode == "ABx":
            ParsedInstruction["A"] = ((Instruction >> 6) & 0xFF)
            ParsedInstruction["Bx"] = ((Instruction >> 14) & 0x3FFFF)
        elif OpMode == "sBx":
            ParsedInstruction["A"] = ((Instruction >> 6) & 0xFF)
            ParsedInstruction["sBx"] = ((Instruction >> 14) & 0x3FFFF) - 131071

        ParsedInstruction["Proto"] = Proto

        return ParsedInstruction

    def ParseProto(self):
        Proto = {
            "Instructions": {},
            "Constants"   : {},
            "Protos"      : {}
        }

        Proto["SourceName"]      = self.Reader.ReadString()
        Proto["LineDefined"]     = self.Reader.ReadInt()
        Proto["LastLineDefined"] = self.Reader.ReadInt()
        Proto["NumUpvalues"]     = self.Reader.ReadByteAsInt()
        Proto["NumParams"]       = self.Reader.ReadByteAsInt()
        Proto["IsVararg"]        = self.Reader.ReadByteAsInt()
        Proto["MaxStackSize"]    = self.Reader.ReadByteAsInt()

        CodeSize = self.Reader.ReadInt()
        for IP in range(1, CodeSize + 1):
            Proto["Instructions"][IP] = self.ParseInstruction(self.Reader.ReadInt(), Proto)
        
        ConstantSize = self.Reader.ReadInt()
        for CI in range(0, ConstantSize):
            ConstantType = self.Reader.ReadByteAsInt()

            if ConstantType == 0:
                Proto["Constants"][CI] = [ConstantType, "nil"]
            elif ConstantType == 1:
                Proto["Constants"][CI] = [ConstantType, self.Reader.ReadByteAsInt()]
            elif ConstantType == 3:
                Proto["Constants"][CI] = [ConstantType, self.Reader.ReadLuaNumber()]
            elif ConstantType == 4:
                Proto["Constants"][CI] = [ConstantType, self.Reader.ReadString()]
            else:
                Logger.Send("Invalid Constant Type", 3)
                exit()

        ProtoSize = self.Reader.ReadInt()
        for PI in range(0, ProtoSize):
            Proto["Protos"][PI] = self.ParseProto()
        
        
        # Debug information (Disregard as we are not decompiling with debug information)

        SourceLinePositionSize = self.Reader.ReadInt()
        for SLPI in range(0, SourceLinePositionSize):
            self.Reader.ReadInt()
            self.Reader.ReadInt()
        
        LocalVariableSize = self.Reader.ReadInt()
        for LVI in range(0, LocalVariableSize):
            self.Reader.ReadString()
            self.Reader.ReadInt()
            self.Reader.ReadInt()
        
        UpvalueSize = self.Reader.ReadInt()
        for UI in range(0, UpvalueSize):
            self.Reader.ReadString()
        

        return Proto

    def ParseHeader(self):
        self.HeaderSignature = self.Reader.ReadInt()
        if self.HeaderSignature != 1635077147:
            # Can be big endian format

            self.Reader.Close()

            self.Reader = Reader(FileName, "big")
            self.HeaderSignature = self.Reader.ReadInt()

            if self.HeaderSignature != 1635077147:
                Logger.Send("Invalid Header Signature", 3)
                exit()
        
        self.VersionNumber = self.Reader.ReadByteAsInt()
        if self.VersionNumber != 0x51:
            Logger.Send("Invalid Version Number", 3)
            exit()

        self.Format = self.Reader.ReadByteAsInt()
        if self.Format != 0:
            Logger.Send("Unofficial bytecode format", 3)
            exit()
        
        self.Endianness = self.Reader.ReadByteAsInt()
        if self.Endianness != (self.Reader.Endianness != "big"):
            Logger.Send("Invalid Endianness", 3)
            exit()
        
        self.IntSize         = self.Reader.ReadByteAsInt()
        self.Size_TSize      = self.Reader.ReadByteAsInt()
        self.InstructionSize = self.Reader.ReadByteAsInt()
        self.LuaNumberSize   = self.Reader.ReadByteAsInt()
        self.IntegralFlag    = self.Reader.ReadByteAsInt()

        self.Reader.IntSize = self.IntSize
        self.Reader.SizeT   = self.Size_TSize
        self.Reader.LuaNumberSize = self.LuaNumberSize


### Writer

class Writer:
    def __init__(self):
        self.Output = ""
        self.IndentSize = 4

        self.IndentLevel = 0
    
    def Append(self, String, NewLine = False):
        self.Output += " " * (self.IndentSize * self.IndentLevel) + String + ("\n" if NewLine else "")

    def Indent(self):
        self.IndentLevel += 1

    def Unindent(self):
        self.IndentLevel -= 1


### Formatter

class Formatter:
    def __init__(self):
        pass

    def FormatConstant(self, Constant):
        ConstantType = Constant[0]

        if ConstantType == 0:
            return "nil"
        elif ConstantType == 1:
            return str(Constant[1])
        elif ConstantType == 3:
            return str(Constant[1])
        elif ConstantType == 4:
            return "\"" + Constant[1] + "\""
        else:
            Logger.Send("Invalid Constant Type", 3)
            exit()


### Opcode Handlers

Writer = Writer()
Formatter = Formatter()

VariableCount = 0
GlobalCount = 0
UpvalueCount = 0

Stack = {}

def Handle_LOADK(Instruction):
    global VariableCount

    Return = "local var" + str(VariableCount) + " = " + Formatter.FormatConstant(Instruction["Proto"]["Constants"][Instruction["Bx"]])
    Stack[Instruction["A"]] = "var" + str(VariableCount)
    
    VariableCount += 1

    return Return, True

def Handle_GETGLOBAL(Instruction):
    global GlobalCount

    Return = "local global" + str(GlobalCount) + " = " + Formatter.FormatConstant(Instruction["Proto"]["Constants"][Instruction["Bx"]]).strip("\"")
    Stack[Instruction["A"]] = "global" + str(GlobalCount)
    
    GlobalCount += 1

    return Return, True

def Handle_CALL(Instruction):
    global VariableCount

    Return = ""

    OldFunctionLocation = Instruction["A"]

    if Instruction["C"] >= 2:
        AmountOfResults = Instruction["C"] - 1

        Return += "local var" + str(VariableCount) + (", " if AmountOfResults > 1 else " = ")
        Stack[Instruction["A"]] = "var" + str(VariableCount)
        VariableCount += 1

        for ResultCount in range(1, AmountOfResults):
            Return += "var" + str(VariableCount) + (", " if ResultCount < AmountOfResults - 1 else " = ")
            Stack[Instruction["A"] + ResultCount] = "var" + str(VariableCount)
            VariableCount += 1
    
    Return += Stack[OldFunctionLocation] + "("
    if Instruction["B"] >= 2:
        AmountOfArguments = Instruction["B"] - 1

        for ArgumentCount in range(1, AmountOfArguments + 1):
            Return += Stack[Instruction["A"] + ArgumentCount] + (", " if ArgumentCount < AmountOfArguments else "")
        
    Return += ")"

    return Return, True

def Handle_RETURN(Instruction):
    Return = "return "

    if Instruction["B"] >= 2:
        AmountOfReturns = Instruction["B"] - 1

        for ReturnCount in range(1, AmountOfReturns + 1):
            Return += Stack[Instruction["A"] + ReturnCount] + (", " if ReturnCount < AmountOfReturns else "")
    
    return Return, True


OpcodeHandlers = {"LOADK":Handle_LOADK, "GETGLOBAL":Handle_GETGLOBAL, "CALL":Handle_CALL, "RETURN":Handle_RETURN}



### Main

Logger = Logger(3)

FileName = "Samples/helloworld32.luac"
File = Reader(FileName)

Data = Parser(File)
Data.Parse()

def HandleProto(Proto):
    for Instruction in Proto["Instructions"].values():
        OpCode = Instruction["OpCode"]

        if OpCode in OpcodeHandlers:
            Text, NewLine = OpcodeHandlers[OpCode](Instruction)
            Writer.Append(Text, NewLine)
        else:
            Logger.Send("Invalid OpCode", 3)
            exit()

    for SubProto in Proto["Protos"].values():
        HandleProto(SubProto)

    print(Writer.Output)

HandleProto(Data.MainProto)