#!/usr/bin/python3

import sys
import re

        
        
class port() :

    def __init__(self, portName, direction, portType, defValue, isClk=False) :
        self.name      = portName
        self.direction = direction
        self.type      = portType
        self.defValue  = defValue
        self.isClk     = isClk

    def getString(self) :
        string = self.name+' : '+self.direction+' '+self.type
        if self.defValue != '' :
            string = string+' := '+self.defValue
        return string 

    def getInst(self) :
        string = self.name+' => '+self.name
        return string

    def getSignalDef(self) :
        string = 'signal '+self.name+' : '+self.type
        return string

        
class generic() :

    def __init__(self, genericName, genericType, defValue) :
        self.name     = genericName
        self.type     = genericType
        self.defValue = defValue

    def getString(self) :
        string = self.name+' : '+self.type
        if self.defValue != '' :
            string = string+' := '+self.defValue
        return string

    def getInst(self) :
        string = self.name+' => '+self.name
        return string

    
class entity() :

    def __init__(self, name) :
        self.name     = name
        self.ports    = []
        self.generics = []

    def addPort(self, port, isClk=False) :
        self.ports.append( port )

    def addGeneric(self, generic) :
        self.generics.append( generic )
        

    def getDef(self, empty=False) :
        
        string = 'entity '+self.name+' is\n'

        if not(empty) :
            if len(self.generics)>0 :
                string = string+'generic (\n'
                for i,gen in enumerate(self.generics) :
                    string = string+gen.getString()
                    if i != len(self.generics)-1 :
                        string = string+';\n'
                    else :
                        string = string+'\n'
    
                string = string+');\n'

            if len(self.ports)>0 :
                string = string+'port (\n'
                for i,por in enumerate(self.ports) :
                    string = string+por.getString()
                    if i != len(self.ports)-1 :
                        string = string+';\n'
                    else :
                        string = string+'\n'
                string = string+');\n'       

        string = string+'end entity '+self.name+';\n'
        
        return string

    def getInst(self, desc):
        
        string = desc+' : entity work.'+self.name+'\n'

        if len(self.generics)>0 :
            string = string+'generic map (\n'
            for i,gen in enumerate(self.generics) :
                string = string+gen.getInst()
                if i != len(self.generics)-1 :
                    string = string+',\n'
                else :
                    string = string+'\n'
    
            string = string+')\n'

        if len(self.ports)>0 :
               
            string = string+'port map(\n'
            for i,por in enumerate(self.ports) :
                string = string+por.getInst()
                if i != len(self.ports)-1 :
                    string = string+',\n'
                else :
                    string = string+'\n'
            string = string+');\n'
        
        return string

    def getArch(self, signals='', body='') :
        archName = self.name+'_arch'
        string = 'architecture '+archName+' of '+self.name+' is\n'
        string = string+signals+'\n'
        string = string+'begin\n'
        string = string+body+'\n'
        string = string+'end '+archName+';\n'

        return string 

    def getSignalDef (self) :
        string = '' 
        for port in self.ports :
            string = string+port.getSignalDef()+';\n'
        return string

    def getTB(self, ent) :

        # entity inst
        body = ent.getInst( 'tb' )

        # clk gen
        body = body+'clk_generation : process\n'
        body = body+'begin\n'
        body = body+'clk <= \'1\';\n'
        body = body+'wait for CLK_PERIOD / 2;\n'
        body = body+'clk <= \'0\';\n'
        body = body+'wait for CLK_PERIOD / 2;\n'
        body = body+'end process clk_generation;\n'
        body = body+'\n\n'
        
        # main process
        body = body+'main_process : process (clk) is\n'
        for i in range(0,10) :
            body = body+'wait for CLK_PERIOD;\n'
        body = body+'end process;\n'
        body = body+'\n\n'
        
        # signals
        clkConst = 'constant CLK_PERIOD : time := 100 ns;\n'
        signals = clkConst+ent.getSignalDef()

        # generate arch
        return self.getArch(signals=signals, body=body)


######### UTILS 
def selectPorts( text ) :
    
    txt = re.sub('\s*--.*', '', text)
    txt = txt.replace('\n', '')
    
    parsed = re.search('port\s*\(.*\)\s*;', txt)
    txt = parsed.group()
    
    txt = re.sub( '\Aport\s*\(', '', txt )
    txt = re.sub( '\)\s*;\Z', '', txt )
    txt = txt.split(';')

    ports = []
    for i,s in enumerate(txt) :

        name = ''
        direction = ''
        type_ = ''
        defValue = ''
        
        txtTmp = re.sub('^\s*', '', s)
        txtTmp = txtTmp.split(':=')
        
        if len(txtTmp)>1 :
            defvalue = txtTmp[1].replace(' ', '')
        name = txtTmp[0].split(':')[0].replace(' ', '')
        direction = re.search('^\s*[a-zA-Z_]*\s*', (txtTmp[0].split(':'))[1] ).group().replace(' ', '')
        type_     = re.search('\s*[a-zA-Z_\(\)]*\s*$', (txtTmp[0].split(':'))[1] ).group().replace(' ', '')
        po = port(name, direction, type_, defValue)
        ports.append(po)
        
    return ports

        
def selectGenerics( text ) :
    
    txt = re.sub('\s*--.*', '', text)
    txt = txt.replace('\n', '')
    
    parsed = re.search('generic\s*\(.*\s*port', txt)
    txt = parsed.group()

    txt = re.sub( '\Ageneric\s*\(', '', txt )
    txt = re.sub( '\)\s*;\s*port\Z', '', txt )
    txt = txt.split(';')

    generics = []
    for i,s in enumerate(txt) :
        txtTmp = re.sub('^\s*', '', s)
        txtTmp = txtTmp.replace(' ', '')
        defValue = ''
        if( txtTmp.find(':=') ):
            defValue = txtTmp.split(':=')[1]
            txtTmp   = txtTmp.split(':=')[0]
        name = txtTmp.split(':')[0]
        genericType = txtTmp.split(':')[1]

        gen = generic(name, genericType, defValue)
        generics.append(gen)

    return generics


def selectEntity( fileIn ) :
    
    body = fileIn.read()
    entityBegin = re.search('entity.*is', body)
    entityEnd   = re.search('end entity.*;', body)

    if( not(entityBegin) ) :
        print('No entity begin found')
        exit()
    if( not(entityEnd) ) :
        print('No entity end found')
        exit()
        
    begin = entityBegin.span()[0]
    end   = entityEnd.span()[1]
    entityTxt = body[begin:end]
        
    entityName = entityBegin.group()
    entityName = entityName.replace(' ', '')
    entityName = entityName.replace('entity', '')
    entityName = entityName.replace('is', '')

    en = entity( entityName )
        
    for gen in selectGenerics( entityTxt ) :
        en.addGeneric(gen)
    for por in selectPorts( entityTxt ) :
        en.addPort(por)

    return en
    

### THE testbench ###
class testBench :

    def __init__(self, fileIn ) :
        f = open( fileIn, 'r' )
        self.entity = selectEntity( f )
        self.testBench = entity( self.entity.name+'_tb' )

    def getTB(self) :

        string = '--\n-- Self Generated VHDL TestBench\n--\n\n'
        string = string+'library IEEE;\n'
        string = string+'use IEEE.STD_LOGIC_1164.all;\n'
        string = string+'use work.emp_data_types.all;\n'
        string = string+'\n'
        string = string+self.testBench.getDef()+'\n'
        entitySignals = self.entity.getSignalDef()
        
        string = string+self.testBench.getTB( self.entity )
        return string

    
############ MAIN ############
def main() :

    tb = testBench( sys.argv[1] )
#    f = open( sys.argv[1], 'r' )
#    e = selectEntity( f )
#    print( e.getDef() )
    print( tb.getTB() )
    
### RUN ###    
main()
