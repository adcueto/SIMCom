import machine
import uasyncio as asyncio
from logging import log
import sys, os, utime
#
"""
VERSION 0.0.10
"""

class SIMCOM(object):
    
    RSSI_LEVEL = {0: "SIN SIGNAL", 1: "SIN SIGNAL", 2:"MARGINAL",3:"MARGINAL",4:"MARGINAL",5:"MARGINAL",6:"MARGINAL", 7:"MARGINAL", 8:"MARGINAL", 9:"MARGINAL",
           10:"OK",11:"OK",12:"OK",13:"OK",14:"OK",
           15:"GOOD",16:"GOOD",17:"GOOD",18:"GOOD",19:"GOOD",
           20:"EXCELENT",21:"EXCELENT",22:"EXCELENT",23:"EXCELENT",24:"EXCELENT",25:"EXCELENT",26:"EXCELENT",27:"EXCELENT",28:"EXCELENT",29:"EXCELENT",30:"EXCELENT",31:"EXCELENT",
           99:"NO NETWORK"   
           }
    
    def __init__(self, uart:int= 0, tx_pin:int=0, rx_pin:int=1, baudrate:int=115200, th_reset:int = 5, th_exit:int=20, module_name:str="Default", en_log:bool = True):
        self.__uart = machine.UART(uart, baudrate=baudrate, tx=machine.Pin(tx_pin), rx=machine.Pin(rx_pin))
        self.__pwr_key = machine.Pin(14, machine.Pin.OUT)
        self.__socketid:int = 0
        self.__enreset:bool = True
        self.__enlog:bool = en_log
        self.__swriter = asyncio.StreamWriter(self.__uart, {})
        self.__sreader = asyncio.StreamReader(self.__uart)
        self.__cretries:int = 0
        self.__threset:int = th_reset
        self.__thexit:int = th_exit
        self.__module_name:str = module_name
  

        
    #power_off
    async def power_off(self):
        response = await self.send_command("AT+CPOWD=1")
        log.resp(response.split(), self.en_log)
        
    #read_reponse
    async def read_reponse(self, length:int = 255, timeout_s:int = 5) ->str:
        """
        Read cellular module serial for AT command responses

        Args:
            timeout_s (int, 5-10): read timeout in seconds. Defaults to 5.

        Returns:
            str: return the reading of the cellular module
        """
        try:
            response = await asyncio.wait_for(await self.__sreader.read(length), timeout_s)
        
        except asyncio.TimeoutError:
            log.error(f'send command timeout from module {self.__module_name}')
            return "ERROR"
        
        except Exception as e:
            sys.print_exception(e)
            return "ERROR"
        
        else:
            return response.decode()
        
    # send_command
    async def send_command(self, command:str, timeout_s:int = 2) -> str:
        """
        Serial AT commands are sent through the serial to the cellular module and the response is received.

        Args:
            command (str): Through the serial
            timeout_s (int, 5-10): read timeout in seconds. Defaults to 10.

        Returns:
            str:  return the reading of the cellular module
        """
        try:
            response = b""
            self.__swriter.write(command +'\r\n')
            await self.__swriter.drain()
            response = await asyncio.wait_for(self.__sreader.read(255), timeout_s)
            self.__sreader._buffer = b''  # clear buffer
            #print(response)
        except asyncio.TimeoutError:
            log.error(f'send command timeout from module {self.__module_name}')
            return "ERROR"
        
        except Exception as e:
            sys.print_exception(e)
            return "ERROR"
        
        else:
            return response.decode()
      
      
    #isReady
    async def isReady(self, timeout=2000) -> bool:
        """_summary_

        Args:
            timeout (int, optional): _description_. Defaults to 2000.

        Returns:
            bool: _description_
        """
        try:
            log.info("Is Ready?")
            response =  await self.send_command("AT")
            log.resp(response.split(), self.__enlog)
            start_time = utime.ticks_ms()
            
            while "OK" not in response: 
                log.info(f'Cellular {self.__module_name} is starting up, please wait..')
                response = await self.send_command("AT")
                log.resp(response.split(), self.__enlog)
                if "ERROR":
                    log.info("Cellular not responding")
                self.__cretries += 1
                await asyncio.sleep(1)
                
                #Apply Reset RF Circuit
                if self.__enreset:
                    await self.send_command("AT+CFUN=0")
                    await asyncio.sleep(5)
                    await self.send_command("AT+CFUN=1")
                    self.__enreset = False
                    
                #More than 10 retries, apply reset
                if self.__cretries == self.__threset:
                    log.info(f"Rebooting the Cellular {self.__module_name} ")
                    await self.reset() #reset
                    await asyncio.sleep(1)
                    
                if self.__cretries == self.__threset + 5:
                    log.info(f"Rebooting the Cellular {self.__module_name}")
                    await self.reset() #reset
                    await asyncio.sleep(1)
                    
                #More than 20 retries, return False, why not modem is not responding
                if self.__cretries == self.__thexit:
                    log.error(f"Modem {self.__module_name} is not responding :(")
                    return False
                
        except Exception as e:
            sys.print_exception(e)
            return False
        
        else:   
            log.info(f'{self.__module_name} is ready')
            return True
        
    #isSimCard   
    async def isSIMCard(self) -> bool:
        try:
            log.info(f"{self.__module_name}: Check SIM Card PIN..")
            response = await self.send_command("AT+CPIN?")
            log.resp(response.split(), self.__enlog)
                
            while ("READY" not in response):
                log.info(f"{self.__module_name} : Please check whether the sim card has been inserted!")
                response = await self.send_command("AT+CPIN?")
                log.resp(response.split(), self.__enlog)
                if "ERROR" not in response:
                    log.info(f"Module {self.__module_name} not responding")
                self.retries += 1
                log.info(f"Retries: {self.retries}")
                await asyncio.sleep(5)
                
                #Apply Reset RF Circuit
                if self.f_rst:
                    await self.send_command("AT+CFUN=2")
                    utime.sleep(5)
                    await self.send_command("AT+CFUN=1")
                    self.f_rst = False
                    
                #More than 10 retries, apply reset
                if self.__cretries == self.__threset:
                    log.info(f"Rebooting {self.__module_name}.. ")
                    self.reset() #reset
                    
                #More than 20 retries, return False, why not modem is not responding
                if self.__cretries == self.__thexit:
                    log.error(f"Moule {self.__module_name} not responding :(")
                    return False
                
        except Exception as e:
            sys.print_exception(e)
            return False
        
        else:
            self.retries = 0
            log.info(f'{self.__module_name}: SIM Card is present')
            return True
                   
    #isRegistered
    async def isRegistered(self):
        #Send the AT command to force network registration:
        #----------------------------------------------------    
            #1:  Registered, home network
            #5:  Registered, roaming
        #----------------------------------------------------    
        #response = self.send_command("AT+CREG?")and "+CREG: 0,5"
        try:
            response = self.send_command("AT+CREG?")
            log.resp(response.split(), self.__enlog)
            while "+CREG: 0,1" not in response:
                log.info(f"The module {self.__module_name} has not been registered, please wait...")
                response = self.send_command("AT+CREG?")
                log.resp(response.split(), self.__enlog)
                self.retries += 1
                await asyncio.sleep(5)

                #Apply Reset RF Circuit
                if self.__enreset:
                    await self.send_command("AT+CFUN=2")
                    await asyncio.sleep(5)
                    await self.send_command("AT+CFUN=1")
                    self.f_rst = False
                #More than 5 retries, apply reset
                if self.__cretries == self.__threset:
                    log.info(f"Rebooting {self.__module_name}..")
                    self.reset() #reset
                    
                #More than 10 retries, return False, why not modem is not responding
                if self.__cretries == self.__thexit:
                    log.error(f"Modem {self.__module_name} is not responding :(")
                    return False
                
        except Exception as e:
            sys.print_exception(e)
            return False
        
        else: 
            self.__cretries = 0
            log.info(f"The modem {self.__module_name} has been registered!")
            return True
        
    #isAttach  
    async def isAttach(self):
        #5-Check for GPRS attachment service status
        try:
            response = await self.send_command("AT+CGATT?")
            log.resp(response.split(), self.__enlog)
            while "OK" not in response:
                log.info('offline, please wait...')
                await self.send_command("AT+CGATT=1")
                log.resp(response.split(), self.__enlog)
                self.retries += 1
                log.info(f"Retries: {self.retries}")
                await asyncio.sleep(5)

                #More than 10 retries, return False, why not modem is not responding
                if self.retries == 10:
                    log.error(f"Modem {self.__module_name} is not responding :(")
                    return False
                
        except Exception as e:
            sys.print_exception(e)
            return False
        
        else:
            self.__cretries = 0
            log.info(f'Modem {self.__module_name} is online')
            return True
        
    #attach 
    async def attach(self):
        log.info(f"{self.__module_name}: Attaching to the network..")
        response = await self.send_command("AT+CGATT=1")
        await asyncio.sleep(2)
        log.resp(response.split(), self.__enlog)
    #datach 
    async def datach(self):
        log.info(f"{self.self.__module_name}: Detaching to the network..")
        response = await self.send_command("AT+CGATT=0")
        log.resp(response.split(), self.__enlog)
        
    #get_battery
    async def get_battery(self, timeout_ms = 1000) -> float:
        try:
            volt:int = 0
            log.info(f"{self.__module_name}: Check Level Battery.. ")
            response = await self.send_command("AT+CBC")
            start_time = utime.ticks_ms()
            while ("OK" not in response) and ((utime.ticks_ms() - start_time) < timeout_ms):
                response = await self.send_command("AT+CBC")
                await asyncio.sleep(1)
            if "ERROR" not in response:
                volt:float = int(response.split(',')[-1].replace("\r\n\r\nOK\r\n", ""))/1000
            
        except Exception as e:
            sys.print_exception(e)
            return 0.0
        
        else:
            return volt
            
    #get_signal       
    async def get_signal(self) -> tuple:
        try:
            signal:int = 0
            log.info(f"{self.__module_name} : Check Network signal quality")
            response = await self.send_command("AT+CSQ")
            if "+CSQ:" in response:
                response = response.split()
                log.resp(response, self.__enlog)
                signal = int(response[response.index("+CSQ:")+1].split(',')[0])                
                
        except Exception as e:
            sys.print_exception(e)
            return 0, "ERROR"
        
        else:   
            return signal, Cellular.RSSI_LEVEL[signal]
        

        
#Add all GSM Modules
class gsm:      
    class SIM800L(Cellular):
        def __init__(self, uart:int= 1, tx_pin:int=4, rx_pin:int=5, baudrate:int=115200, th_reset:int = 10, th_exit:int=20, module_name ="SIM800L", en_log = True):
            super().__init__(uart, tx_pin, rx_pin, baudrate, th_reset, th_exit,module_name,en_log)
            self.__rst = machine.Pin(3, machine.Pin.OUT)
            self.__enlog = en_log
            
        #power on/off the module
        async def reset(self):
            log.info("Reset SIM800L")
            self.__rst.value(0)
            await asyncio.sleep(2)
            self.__rst.value(1)
            await asyncio.sleep(5)
        
        async def start(self) -> bool:
            #0-Reset ON:
            log.info('Rebooting SIM800L')
            await self.reset()
            await asyncio.sleep(5)
            
            #1-Check if SIM800L is ready
            if not await self.isReady():
                return False
            
            #Disable jamming detection
            log.info("Disable jamming detection")
            response = await self.send_command("AT+SJDR=0")
            log.resp(response.split(), self.__enlog)
            
            #Disable Initial URC Presentation
            log.info("Disable Initial URC Presentation")
            response = await self.send_command("AT+CIURC=0")
            if "OK" not in response:
                response = await self.send_command("AT+CIURC=0")
            log.resp(response.split(), self.__enlog)
            
            #-Cheack Battery
            volt =  await self.get_battery()
            log.info(f"Battery Voltage: {volt}")
                
            #3-Check SIM Card PIN
            if not await self.isSIMCard(): return False

            return True
        
        #tcp_init
        async def tcp_init(self)->bool:
       
            #1-Network signal quality query, returns a signal value
            level, signal = await self.get_signal()
            log.info(f"Signal status: {signal}")
            if signal == "SIN SIGNAL": return False
        
            #2-Check SIM Card PIN
            if not await self.isSIMCard(): return False
            
            #3-Check Network Registration Status
            if not await self.isRegistered(): return False
            
            #4-Check for GPRS attachment service status
            if not await self.isAttach(): return False

            return True
        
        #connect_gprs
        async def connect_gprs(self, apn, user, password):
            # Set APN, username, and password
            log.info("Set APN, username, and password")
            response = await self.send_command("AT+CSTT?")
            log.resp(response.split(), self.__enlog)
            if apn not in  response:
                response= await self.send_command('AT+CSTT="{}","{}","{}"'.format(apn, user, password))
                log.resp(response.split(), self.__enlog)
            
            # Bring up wireless connection
            log.info("Bring up wireless connection")
            response = await self.send_command("AT+CIICR", 10000)
            log.resp(response.split(), self.__enlog)
            #Wait for bringup
            await asyncio.sleep(6)
            
            # Check if connection is successful
            response = await self.send_command("AT+CIFSR", 10000)
            log.resp(response.split(), self.__enlog)
            if "ERROR" in response:
                log.error("GPRS connection failed")
                return False
            log.info("GPRS connection is successful")
            
            return True
        
        #tcp_connection
        async def tcp_connection(self, server, port):
            try:
                retries:int = 0
                # Start TCP connection
                log.info("Start TCP connection")
                response = await self.send_command('AT+CIPSTART="TCP","{}",{}'.format(server, port))
                log.resp(response.split(), self.__enlog)
                
                # Check if connection is successful
                log.info("Check connection")
                response = await self.send_command("AT+CIPSTATUS")
                log.resp(response.split(), self.__enlog)
                
                while "CONNECT OK" not in response:
                    retries += 1
                    log.error("TCP connection failed, wait...")
                    response = await self.send_command("AT+CIPSTATUS")
                    log.resp(response.split(), self.__enlog)
                    await asyncio.sleep(1)
                    if retries >20:
                        return False
               
            except Exception as e:
                sys.print_exception(e)
                return False
            
            else:
                log.info("TCP connection successful")
                return True
            
        #send_tcp_data 
        async def send_tcp_data(self,data):
            try:
                # Set data length for sending
                log.info("Sending data...")
                response = await self.send_command('AT+CIPSEND={}'.format(len(data)))
                log.resp(response.split(), self.__enlog)
                
                # Send data
                response = await self.send_command(data)
                log.resp(response.split(), self.__enlog)
                
                # Wait for response
                await asyncio.sleep(1)
                
            except Exception as e:
                sys.print_exception(e)
                return False
            
            else:
                return True
            
        #read_tcp_data
        async def read_tcp_data(self):
            try:
                # Wait for response
                await asyncio.sleep(1)
                response = await read_response(255)#self.uart.read(self.uart.any()).decode('utf-8')
                if response == "":
                    return "NO DATA"
                       
            except Exception as e:
                sys.print_exception(e)
                return "ERROR"
            
            else:  
                return response

        #close_tcp
        async def close_tcp(self):
            # Close TCP connection
            log.info("Close tcp connection")
            response = await self.send_command("AT+CIPCLOSE")
            log.resp(response.split(), self.__enlog)
            
            # Deactivate GPRS connection
            response = await self.send_command("AT+CIPSHUT")
            log.resp(response.split(), self.__enlog)
        
        #enable_jamming
        async def enable_jamming(self):
            response = await self.send_command("AT+SJDR=1,0,40,0")  #50
            log.resp(response.split(), self.__enlog)
        
        #disable_jamming
        async def disable_jamming(self):
            response = await self.send_command("AT+SJDR=0")
            log.resp(response.split(), self.__enlog)
            
        #isJamming
        async def isJamming(self) -> bool:
            try:
                response = await self.send_command("AT+SJDR?")
                log.resp(response.split(), self.__enlog)
                if '1,0,40,0,1' in response:
                    return True
            except Exception as e:
                sys.print_exception(e)
                return False
            
            else:
                return False
                    
            
#Add all LTE Modules        
class lte:
    class SIM7080G(Cellular):
        #NETWORK MODE
        LTE:int = 38
        GSM:int = 13
        LTE_GSM:int = 51
        AUTOMATIC:int= 2
        
        #LTE MODE
        LTE_NB:int = 2
        LTE_CATM:int = 1
        
        def __init__(self, uart:int= 0, tx_pin:int=0, rx_pin:int=1, baudrate:int=115200, th_reset:int = 10, th_exit:int=20, module_name = "SIM7080G", en_log:bool = True):
            super().__init__(uart, tx_pin, rx_pin, baudrate, th_reset, th_exit, module_name, en_log)
            self.__enlog = en_log
            #power on/off the module
        async def reset(self):
            """
            System power on/off control
            ---------------------------------------------------------
            After the PWRKEY continues to pull-down more than 12S, the system
            will automatically reset
            ---------------------------------------------------------
            """
            log.info('Clase PADRE lte RESET')
            self.__pwr_key.value(1)
            await asyncio.sleep(2)
            self.__pwr_key.value(0)
            await asyncio.sleep(2)
            
        async def start(self):
            """
            Before starting, check the module and SIM card are connected
            ---------------------------------------------------------
            Parameters: Self
                        timeout: wait time
            Returns:
                True: success 
            --------------------------------------------------------
            """
            #0 - reset
            log.info("Rebooting SIM7080G")
            #await self.reset()
            #await asyncio.sleep(5)
            
            #2-Check if SIM800L is ready
            if not await self.isReady():
                return False
            
            #0-Disable jamming detection
            log.info("Disable Engineering Mode")
            response = await self.send_command("AT+CENG=0,1")
            log.resp(response.split(), self.__enlog)
            
            #1-Disable URC Report Configuration
            log.info("Disable URC Report Configuration")
            response = await self.send_command('AT+CURCCFG="QUALCOMM",0')
            log.resp(response.split(), self.__enlog)
            
            #3-Check if SIM Card is ready
            if not await self.isSIMCard():
                return False
            
            return True
        
        async def setup_tcp(self):
            log.info("Setup configuration")
            response = await self.send_command("AT+CACFG?")
            log.resp(response.split(), self.__enlog)
            await asyncio.sleep(1)
            response = await self.send_command('AT+CACFG="TRANSWAITTM",5')
            log.resp(response.split(), self.__enlog)
            await asyncio.sleep(1)
            response = await self.send_command('AT+CACFG="TRANSPKTSIZE",1024')
            log.resp(response.split(), self.__enlog)
            await asyncio.sleep(1)
            response = await self.send_command('AT+CACFG="TIMEOUT",0,10')
            log.resp(response.split(), self.__enlog)
            
            
        async def set_lte_mode(self, mode:int = 3):
            """
            Select LTE Mode
            :param mode: 
            <mode>  1 CAT-M
                    2 NB-Iot
                    3 CAT-M and NB-IoT
            :return: None
            """
            #Select NB-IoT mode,if Cat-M，please set to 1
            response = await self.send_command(f"AT+CMNB={mode}")
            log.resp(response.split(), self.__enlog)
            
            while "OK" not in response:
                response = await self.send_command(f"AT+CMNB={mode}")
                log.resp(response.split(), self.__enlog)
                await asyncio.sleep(1)
                
        #set_network_mode     
        async def set_network_mode(self, mode:int=38):
            """
            Select Network Mode
            :param mode: 
            <mode>  2 Automatic
                    13 GSM only
                    38 LTE only
                    51 GSM and LTE only
            :return: None
            """
            log.info("Setting to Cat-M mode")
            response = await self.send_command("AT+CFUN=0", 5)
            log.resp(response.split(), self.__enlog)
            await asyncio.sleep(1)
            
            response = await self.send_command("AT+CNMP=38")
            log.resp(response.split(), self.__enlog)
            while "OK" not in response:
                response = await self.send_command("AT+CNMP=38")
                log.resp(response.split(), self.__enlog)
                await asyncio.sleep(1)

            response = await self.send_command("AT+CFUN=1", 5)
            log.resp(response.split(), self.__enlog)
        
        #set apn
        async def set_apn(self, apn):
            response = await self.send_command("AT+CGNAPN")
            log.resp(response.split(), self.__enlog)
            
            if apn not in response:
                response = await self.send_command("AT+CNCFG=0,1,{}".format(apn))
                log.resp(response.split(), self.__enlog)
            
        
        #Activate the network bearer   
        async def activate_context(self):
            response = await self.send_command("AT+CNACT?")
            log.resp(response.split(), self.__enlog)
            
            response = await self.send_command("AT+CNACT=0,1")
            log.resp(response.split(), self.__enlog)
            
            if "OK" not in response:
                log.error("Context not activated")
                return False
            return True
        
        #deactivate_context
        async def deactivate_context(self):
            response = await self.send_command("AT+CGACT=0,0")
            log.resp(response.split(), self.__enlog)
            
        #open_socket
        async def open_socket(self, address, port):
            try:
                response = await self.send_command("AT+CASSLCFG?")
                log.resp(response.split(), self.__enlog)
                
                response = await self.send_command("AT+CAOPEN?")
                log.resp(response.split(), self.__enlog)
                
                command = "AT+CASSLCFG=0,{},{}".format("SSL", 0)
                response = await self.send_command(command)
                
                while "OK" not in response:
                    response = await self.send_command(command)
                    log.resp(response.split(), self.__enlog)
                    await asyncio.sleep(1)
                log.resp(response.split(), self.__enlog)
                
                command = "AT+CAOPEN=0,0,{},{},{}".format("TCP", address, port)
                response = await self.send_command(command)
                log.resp(response.split(), self.__enlog)
                
                while "OK" not in response:
                    response = await self.send_command(command)
                    log.resp(response.split(), self.__enlog)
                    await asyncio.sleep(1)
                
            except Exception as e:
                sys.print_exception(e)
                return False
            else:
                return True   
            
        async def close_socket(self):
            #command = "AT+CACLOSE={}".format(socket_id)
            response = await self.send_command("AT+CACLOSE=0")
            log.resp(response.split(), self.__enlog)
            
            response = await self.send_command("AT+CNACT=0,0")
            log.resp(response.split(), self.__enlog)
        
        #send_tcp_data
        async def send_tcp_data(self, data) -> bool:
            #command = "AT+CSOSEND={},{}".format(socket_id, len(data))
            print("Send Data: {}".format(data))
            command = "AT+CASEND=0,{}".format(len(data))
            response = await self.send_command(command)
            log.resp(response.split(), self.__enlog)
            
            if "ERROR" in response:
                log.info("Data not sent")
                return False
            
            #Wait for response >
            while ">" not in response:
                response = await self.read_response()
                await asyncio.sleep(1)
                
            # Send data
            log.info("Send Data")
            #self.uart.write((data +'\r\n').encode())
            response = await self.send_command((data +'\r\n').encode())
            log.resp(response.split(), self.__enlog)
            
            # Wait for response
            await asyncio.sleep(1)
            return True

        #read_tcp_data     
        async def read_tcp_data(self):
            response = await self.send_command("AT+CARECV=0,1024")
            log.resp(response.split(), self.b_log)
            if "+CARECV: " in response:
                length = response.split("+CARECV: ")[1].split("\r\n")[0]
                data = await self.read_response(length = int(length))#self.uart.read(int(length)).decode()
                return data
                
        #get_gps_status  
        async def get_gps_status(self,timeout=10000) ->tuple:
            try:
                log.info("Start GPS session...")
                response = await self.send_command('AT+SGNSCFG="MODE",0')
                log.resp(response.split(), self.__enlog)
                response = await self.send_command("AT+CGNSPWR=0")
                log.resp(response.split(), self.__enlog)
                await asyncio.sleep(1)
                response = await self.send_command("AT+CGNSPWR=1")
                log.resp(response.split(), self.__enlog)
                await asyncio.sleep(1)
                c_gps:int = 0
                start_time = utime.ticks_ms()
                
                while (utime.ticks_ms() - start_time ) < timeout:
                    response = await self.send_command("AT+CGNSINF")
                    log.resp(response.split(), self.__enlog)
                    c_gps += 1
                    
                    #Reset GPS
                    if ',,,,' in response:
                        #GNSS Power Control
                        if c_gps == 15:
                            log.info("GNSS Power Control")
                            await self.send_command("AT+CGNSPWR=0")
                            await asyncio.sleep(1)
                            await self.send_command("AT+CGNSPWR=1")
                            await asyncio.sleep(1)
                                
                         #More than RETRY_EXIT, return False
                        if c_gps == 20:
                            log.error("SIM7080G GPS is not responding :(")
                            return (0,0.0, 0.0, 0)
                    #info
                    else:
                        #if "" not in response:
                        resp = response.split()
                        if "+CGNSINF:" in resp:
                            resp = resp[resp.index("+CGNSINF:")+1].split(",")
                            fix = resp[1];lat = resp[3]; lon = resp[4];sat = resp[14]
                            log.info(f"GPS Info: Fix: {fix}, Lat: +{lat}, Lon: {lon}, Sat: {sat}")
                            if fix == "1":
                                return (int(fix),float(lat),float(lon),int(sat))  #Fix
                    await asyncio.sleep(1)
                
            except Exception as e:
                sys.print_exception(e)
                return (0,0,0,0) #error

            else:
                return (0,0,0,0) #timeout