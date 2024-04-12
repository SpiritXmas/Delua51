## Delua 5.1 - A Lua 5.1 decompiler, aimed towards compiled lua files with stripped debug information.



### Reader

class Reader:
    def __init__(self, FileName):
        self.Pointer = 0
        self.File = open(FileName, "rb")

        self.endian = None
        self.SizeT = 4
    
    def ReadByte(self):
        self.Pointer += 1
        return self.File.read(1)
    
    def ReadByteAsInt(self):
        self.Pointer += 1
        return int.from_bytes(self.File.read(1), self.endian or "little")
    
    def ReadBytes(self, Amount):
        self.Pointer += Amount
        return self.File.read(Amount)
    
    def ReadInt(self):
        self.Pointer += 4
        return int.from_bytes(self.File.read(4), self.endian or "little")
    
    def ReadString(self):
        Size = self.ReadInt()
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


