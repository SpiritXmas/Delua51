## Delua 5.1 - A Lua 5.1 decompiler, aimed towards compiled lua files with stripped debug information.



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


### Parser

class Parser:
    def __init__(self, ReaderObject):
        self.Reader = ReaderObject

    def Parse(self):
        self.ParseHeader()
        self.MainProto = self.ParseProto()

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
            Proto["Instructions"][IP] = self.Reader.ReadInt()
        
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



        

### Main

Logger = Logger(3)

FileName = "Samples/helloworld32.luac"
File = Reader(FileName)

Data = Parser(File)
Data.Parse()

