#!/usr/bin/python3

# Python Plugin LG ThinQ API v2 integration.
# AWHP test version
#
# Author: majki mod superprzemo
#
"""
<plugin key="LG_ThinQ" name="LG ThinQ" author="majki" version="1.2.0 mod superprzemo" externallink="https://github.com/majki09/domoticz_lg_thinq_plugin">
    <description>
        <h2>LG ThinQ domoticz plugin</h2><br/>
        Plugin uses LG API v2. All API interface (with some mods) comes from <a href="https://github.com/no2chem/wideq"> github.com/no2chem/wideq</a>.<br/><br/>
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Reading unit parameters from LG ThinQ API</li>
            <li>Control unit with LG ThinQ API</li>
        </ul>
        <h3>Tested and working devices</h3>
        <h4>Air Conditioners (AC)</h4>
        <ul style="list-style-type:square">
            <li>LG AP12RT NSJ</li>
            <li>LG PC12SQ</li>
        </ul>
        <h4>Air-to-Water Heat Pumps (AWHP)</h4>
        <ul style="list-style-type:square">
            <li>LG therma V 7kW HN0916M NK4</li>
        </ul>
        <br/>
    </description>
    <params>
        <param field="Mode3" label="country" width="50px" />
        <param field="Mode4" label="language" width="50px" />
        <param field="Mode6" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug"/>
                <option label="False" value="Normal" default="true" />
            </options>
        </param>
        <param field="Mode1" label="Device type" width="270px">
            <options>
                <option label="Air Conditioning (AC)" value="type_ac" default="true" />
                <option label="Air to Water Heat Pump (AWHP)" value="type_awhp" default="false" />
            </options>
        </param>
        <param field="Mode2" label="Device ID" width="270px"/>
    </params>
</plugin>
"""
        
        
import Domoticz
import json
import random

import example
import wideq


class BasePlugin:
    enabled = False
    heartbeat_counter = 0
    
    ac_status = None
    
    def __init__(self):
        self.device_id = ""
        self.operation = ""
        self.op_mode = ""
        self.target_temp = ""
        self.hot_water_temp = ""
        self.room_temp = ""
        self.in_water_temp = ""
        self.out_water_temp = ""
        self.cur_temp = ""
        self.goraca_woda = ""
        self.wind_strength = ""
        self.h_step = ""
        self.v_step = ""
        self.tryb_mode = ""
#        self.tryb_silent = ""
        # self.power = ""
        
        self.lg_device = None
        self.state = {}

    def onStart(self):
        if Parameters["Mode6"] == "Debug":
            Domoticz.Debugging(1)
            
        # import web_pdb; web_pdb.set_trace()
        # load config from Domoticz Configuration
        # self.state["gateway"] = getConfigItem(Key="gateway")
        # self.state["auth"] = getConfigItem(Key="auth")
        self.state["gateway"] = {}
        self.state["auth"] = {}
            
        try:
            # read AC parameters and Client state
            self.lg_device, self.state = example.example(Parameters["Mode3"], Parameters["Mode4"], False, Parameters["Mode2"],
                                                  state=self.state)
            
        except IOError:
            Domoticz.Error("wideq_state.json status file missing or corrupted.")
        except AttributeError:
            Domoticz.Error("You don't have any compatible (LG API V2) devices.")
        except UserWarning:
            Domoticz.Error("Device not found on your LG account. Check your device ID.")
            
        # store Client state into Domoticz Configuration
        if getConfigItem(Key="gateway") != self.state["gateway"]:
            setConfigItem(Key="gateway", Value=self.state["gateway"])
            Domoticz.Log("LG API2 (gateway) config saved do Domoticz Configuration.")
        if getConfigItem(Key="auth") != self.state["auth"]:
            setConfigItem(Key="auth", Value=self.state["auth"])
            Domoticz.Log("LG API2 (auth) config saved do Domoticz Configuration.")

        # AC part
        if Parameters["Mode1"] == "type_ac" and self.lg_device is not None:
            Domoticz.Log("Getting AC status successful.")
            if len(Devices) == 0:
                Domoticz.Device(Name="Operation", Unit=1, Image=16, TypeName="Switch", Used=1).Create()
                
                Options = {"LevelActions" : "|||||",
                           "LevelNames" : "|Auto|Cool|Heat|Fan|Dry",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Mode", Unit=2, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
                Domoticz.Device(Name="Target temp", Unit=3, Type=242, Subtype=1, Image=15, Used=1).Create()
                Domoticz.Device(Name="Room temp", Unit=4, TypeName="Temperature", Used=1).Create()
                
                Options = {"LevelActions" : "|||||||",
                           "LevelNames" : "|Auto|L2|L3|L4|L5|L6",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Fan speed", Unit=5, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
                
                
                Options = {"LevelActions" : "||||||||||",
                           "LevelNames" : "|Left-Right|None|Left|Mid-Left|Centre|Mid-Right|Right|Left-Centre|Centre-Right",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "1"}
                           
                Domoticz.Device(Name="Swing Horizontal", Unit=6, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
                
                
                Options = {"LevelActions" : "|||||||||",
                           "LevelNames" : "|Top-Bottom|None|Top|1|2|3|4|Bottom",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "1"}
                           
                Domoticz.Device(Name="Swing Vertical", Unit=7, TypeName="Selector Switch", Image=7, Options=Options, Used=1).Create()
                # Domoticz.Device(Name="Power", Unit=8, TypeName="kWh", Used=1).Create()
                
                Domoticz.Log("LG ThinQ AC device created.")
                
        # AWHP part
        elif Parameters["Mode1"] == "type_awhp" and self.lg_device is not None:
            Domoticz.Log("Getting AWHP status successful.")
            if len(Devices) == 0:
                Domoticz.Device(Name="Operation", Unit=1, Image=16, TypeName="Switch", Used=1).Create()
                
                Options = {"LevelActions" : "||||",
                           "LevelNames" : "|Cool|AI|Heat",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Mode", Unit=2, TypeName="Selector Switch", Image=16, Options=Options, Used=1).Create()
                Domoticz.Device(Name="Target temp", Unit=3, Type=242, Subtype=1, Image=15, Used=1).Create()
                Domoticz.Device(Name="Hot water temp", Unit=4, Type=242, Subtype=1, Image=15, Used=1).Create()
                Domoticz.Device(Name="Input water temp", Unit=5, TypeName="Temperature", Used=1).Create()
                Domoticz.Device(Name="Output water temp", Unit=6, TypeName="Temperature", Used=1).Create()
                Domoticz.Device(Name="Room temp", Unit=7, TypeName="Temperature", Used=1).Create()
                Domoticz.Device(Name="Hot water", Unit=8, TypeName="Temperature", Used=1).Create()

                Options = {"LevelActions" : "|||",
                           "LevelNames" : "|Air|Water",
                           "LevelOffHidden" : "true",
                           "SelectorStyle" : "0"}
                           
                Domoticz.Device(Name="Heating mode", Unit=9, TypeName="Selector Switch", Image=15, Options=Options, Used=1).Create()
                
                
#                Options = {"LevelActions" : "|||",
#                           "LevelNames" : "|OFF|ON",
#                           "LevelOffHidden" : "true",
#                           "SelectorStyle" : "0"}
                           
#                Domoticz.Device(Name="Tryb Silent", Unit=10, TypeName="Selector Switch", Image=15, Options=Options, Used=1).Create()
				
                
                Domoticz.Log("LG ThinQ AWHP device created.") 
        else:
            Domoticz.Error("Getting LG device status failed.")

        DumpConfigToLog()

    def onStop(self):
        Domoticz.Log("onStop called")
        # self.lg_device.monitor_stop()
        
    def onConnect(self, Connection, Status, Description):
        pass

    def onMessage(self, Connection, Data):
        # Domoticz.Log("onMessage called with: "+Data["Verb"])
        # DumpDictionaryToLog(Data)
        
        pass
            
    def onCommand(self, Unit, Command, Level, Hue):
        # Domoticz.Debug("Command received U="+str(Unit)+" C="+str(Command)+" L= "+str(Level)+" H= "+str(Hue))
        # import web_pdb; web_pdb.set_trace()
        
        # AC part
        if Parameters["Mode1"] == "type_ac":
            if (Unit == 1): # Operation
                if(Command == "On"):
                    self.operation = 1
                    self.lg_device.set_on(True)
                    Devices[1].Update(nValue = 1, sValue = "100") 
                else:
                    self.operation = 0
                    self.lg_device.set_on(False)
                    Devices[1].Update(nValue = 0, sValue = "0") 
                    
            if (Unit == 2): # opMode
                newImage = 16
                if (Level == 10):
                    self.lg_device.set_mode(wideq.ACMode.ACO)
                    newImage = 16
                elif (Level == 20):
                    self.lg_device.set_mode(wideq.ACMode.COOL)
                    newImage = 16
                elif (Level == 30):
                    self.lg_device.set_mode(wideq.ACMode.HEAT)
                    newImage = 15
                elif (Level == 40):
                    self.lg_device.set_mode(wideq.ACMode.FAN)
                    newImage = 7
                elif (Level == 50):
                    self.lg_device.set_mode(wideq.ACMode.DRY)
                    newImage = 16
                Devices[2].Update(nValue = self.operation, sValue = str(Level), Image = newImage)
                    
            if (Unit == 3): # SetPoint
                # import web_pdb; web_pdb.set_trace()
                if(Devices[3].nValue != self.operation or Devices[3].sValue != Level):
                    self.lg_device.set_celsius(int(Level))
                    Domoticz.Log("new Setpoint: " + str(Level))
                    Devices[3].Update(nValue = self.operation, sValue = str(Level))
                    
            if (Unit == 5): # Fan speed
                # import web_pdb; web_pdb.set_trace()
                if (Level == 10):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.NATURE)
                elif (Level == 20):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.LOW)
                elif (Level == 30):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.LOW_MID)
                elif (Level == 40):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.MID)
                elif (Level == 50):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.MID_HIGH)
                elif (Level == 60):
                    self.lg_device.set_fan_speed(wideq.ACFanSpeed.HIGH)
                Devices[5].Update(nValue = self.operation, sValue = str(Level))
                    
            if (Unit == 6): # Swing horizontal
                if (Level == 10):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.ALL)
                elif (Level == 20):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.OFF)
                elif (Level == 30):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.ONE)
                elif (Level == 40):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.TWO)
                elif (Level == 50):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.THREE)
                elif (Level == 60):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.FOUR)
                elif (Level == 70):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.FIVE)
                elif (Level == 80):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.LEFT_HALF)
                elif (Level == 90):
                    self.lg_device.set_horz_swing(wideq.ACHSwingMode.RIGHT_HALF)
                Devices[6].Update(nValue = self.operation, sValue = str(Level))
                    
            if (Unit == 7): # Swing vertical
                if (Level == 10):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.ALL)
                elif (Level == 20):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.OFF)
                elif (Level == 30):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.ONE)
                elif (Level == 40):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.TWO)
                elif (Level == 50):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.THREE)
                elif (Level == 60):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.FOUR)
                elif (Level == 70):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.FIVE)
                elif (Level == 80):
                    self.lg_device.set_vert_swing(wideq.ACVSwingMode.SIX)
                Devices[7].Update(nValue = self.operation, sValue = str(Level))
                
            
        # AWHP part
        if Parameters["Mode1"] == "type_awhp":
            if (Unit == 1): # Operation
                if(Command == "On"):
                    self.operation = 1
                    self.lg_device.set_on(True)
                    Devices[1].Update(nValue = 1, sValue = "100") 
                else:
                    self.operation = 0
                    self.lg_device.set_on(False)
                    Devices[1].Update(nValue = 0, sValue = "0") 
                    
            if (Unit == 2): # opMode
                newImage = 16
                if (Level == 10):
                    self.lg_device.set_mode(wideq.ACMode.COOL)
                    newImage = 16
                elif (Level == 20):
                    self.lg_device.set_mode(wideq.ACMode.AI)
                    newImage = 16
                elif (Level == 30):
                    self.lg_device.set_mode(wideq.ACMode.HEAT)
                    newImage = 15
                Devices[2].Update(nValue = self.operation, sValue = str(Level), Image = newImage)
                    
            if (Unit == 3): # Target temp
                if(Devices[3].nValue != self.operation or Devices[3].sValue != Level):
                    self.lg_device.set_celsius(int(Level))
                    Domoticz.Log("new Target temp: " + str(Level))
                    Devices[3].Update(nValue = self.operation, sValue = str(Level))
                    
            if (Unit == 4): # Hot water temp
                if(Devices[4].nValue != self.operation or Devices[4].sValue != Level):
                    self.lg_device.set_hot_water(int(Level))
                    Domoticz.Log("new Hot water Target temp: " + str(Level))
                    Devices[4].Update(nValue = self.operation, sValue = str(Level))
					
            if (Unit == 9): # tryb grzania  - Heating mode
                newImage = 15
                if (Level == 10):
                   self.lg_device.tryb_mode(wideq.ACAWHPswitch.AIR)
                   newImage = 15
                elif (Level == 20):
                    self.lg_device.tryb_mode(wideq.ACAWHPswitch.WATER)
                    newImage = 15
                Devices[9].Update(nValue = self.operation, sValue = str(Level), Image = newImage)	

#            if (Unit == 10): # tryb silent
#                newImage = 15
#                if (Level == 10):
#                   self.lg_device.tryb_silent(wideq.ACAWHPSilent.OFF)
#                   newImage = 15
#                elif (Level == 20):
#                    self.lg_device.tryb_silent(wideq.ACAWHPSilent.ON)
#                    newImage = 15
#                Devices[10].Update(nValue = self.operation, sValue = str(Level), Image = newImage)				
        
    def onDisconnect(self, Connection):
        Domoticz.Log("onDisconnect called")
        # self.lg_device.monitor_stop()

    # every 5 seconds
    def onHeartbeat(self):
        # Domoticz.Log("onHeartbeat called: "+str(self.heartbeat_counter))
        if (self.heartbeat_counter % 6) == 0:
            # Domoticz.Log("onHeartbeat %6 called: "+str(self.heartbeat_counter))
            # import web_pdb; web_pdb.set_trace()
            # to check if self.lg_device has been already read out from server
            if self.lg_device is not None:
        
                try:
                    self.lg_device_status = self.lg_device.get_status()
                    
                    # AC part
                    if Parameters["Mode1"] == "type_ac":
                        self.operation = self.lg_device_status.is_on
                        if self.operation == True:
                            self.operation = 1
                        else:
                            self.operation = 0
                            
                        self.op_mode = self.lg_device_status.mode.name
                        self.target_temp = str(self.lg_device_status.temp_cfg_c)
                        self.room_temp = str(self.lg_device_status.temp_cur_c)
                        self.wind_strength = self.lg_device_status.fan_speed.name
                        self.h_step = self.lg_device_status.horz_swing.name
                        self.v_step = self.lg_device_status.vert_swing.name
                        # self.power = str(self.lg_device_status.energy_on_current)
                        
                    # AWHP part
                    if Parameters["Mode1"] == "type_awhp":
                        self.operation = self.lg_device_status.is_on
                        if self.operation == True:
                            self.operation = 1
                        else:
                            self.operation = 0
                            
                        self.op_mode = self.lg_device_status.mode.name
                        self.target_temp = str(self.lg_device_status.temp_cfg_c)
                        self.hot_water_temp = str(self.lg_device_status.temp_hot_water_cfg_c)
                        self.in_water_temp = str(self.lg_device_status.in_water_cur_c)
                        self.out_water_temp = str(self.lg_device_status.out_water_cur_c)
                        self.cur_temp = str(self.lg_device_status.temp_cur_c)
                        self.goraca_woda = str(self.lg_device_status.temp_hot_water_cur_c)
                        self.tryb_mode = self.lg_device_status.awhp_switch.name
#                        self.tryb_silent = self.lg_device_status.awhp_silent.name
                        
                    self.update_domoticz()
                        
                except wideq.NotLoggedInError:
                    # load config from Domoticz Configuration
                    self.state["gateway"] = getConfigItem(Key="gateway")
                    self.state["auth"] = getConfigItem(Key="auth")
            
                    # read AC parameters and Client state
                    Domoticz.Log("Session expired, refreshing...")
                    self.lg_device, self.state = example.example(Parameters["Mode3"], Parameters["Mode4"], False,
                                                          Parameters["Mode2"], state=self.state)
                    setConfigItem(Key="state", Value=self.state)
                    
                    # store Client state into Domoticz Configuration
                    if getConfigItem(Key="gateway") != self.state["gateway"]:
                        setConfigItem(Key="gateway", Value=self.state["gateway"])
                    if getConfigItem(Key="auth") != self.state["auth"]:
                        setConfigItem(Key="auth", Value=self.state["auth"])
                            
        self.heartbeat_counter = self.heartbeat_counter + 1
        if self.heartbeat_counter > 60:
            self.heartbeat_counter = 0
        
    def update_domoticz(self):
        # import web_pdb; web_pdb.set_trace()
        # AC part
        if Parameters["Mode1"] == "type_ac":
            # Operation
            if (self.operation == 0):
                if (Devices[1].nValue != 0):
                    Devices[1].Update(nValue = 0, sValue ="0") 
                    Domoticz.Log("operation received! Current: " + str(self.operation))
            else:
                if (Devices[1].nValue != 1):
                    Devices[1].Update(nValue = 1, sValue ="100")
                    Domoticz.Log("operation received! Current: " + str(self.operation))
                
            # Mode (opMode)
            if (self.op_mode == "ACO"):
                sValueNew = "10" #Auto
                newImage = 16
            elif (self.op_mode == "COOL"):
                sValueNew = "20" #Cool
                newImage = 16
            elif (self.op_mode == "HEAT"):
                sValueNew = "30" #Heat
                newImage = 15
            elif (self.op_mode == "FAN"):
                sValueNew = "40" #Fan
                newImage = 7
            elif (self.op_mode == "DRY"):
                sValueNew = "50" #Dry
                newImage = 16
                
            if(Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew):
                Devices[2].Update(nValue = self.operation, sValue = sValueNew, Image = newImage)
                Domoticz.Log("Mode received! Current: " + self.op_mode)
                
            # Target temp (tempState.target)
            if (Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp):
                Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
                Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                    
            # Room temp (tempState.current)
            if (Devices[4].sValue != self.room_temp):
                Devices[4].Update(nValue = 0, sValue = self.room_temp)
                Domoticz.Log("tempState.current received! Current: " + self.room_temp)
            # else:
                # Domoticz.Log("Devices[4].sValue=" + Devices[4].sValue)
                # Domoticz.Log("room_temp=" + self.room_temp)
                
            # Fan speed (windStrength)
            if (self.wind_strength == "NATURE"):
                sValueNew = "10" #Auto
            elif (self.wind_strength == "LOW"):
                sValueNew = "20" #2
            elif (self.wind_strength == "LOW_MID"):
                sValueNew = "30" #3
            elif (self.wind_strength == "MID"):
                sValueNew = "40" #4
            elif (self.wind_strength == "MID_HIGH"):
                sValueNew = "50" #5
            elif (self.wind_strength == "HIGH"):
                sValueNew = "60" #6
                    
            if (Devices[5].nValue != self.operation or Devices[5].sValue != sValueNew):
                Devices[5].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("windStrength received! Current: " + self.wind_strength)
                
            # Swing Horizontal (hStep)
            if (self.h_step == "ALL"):
                sValueNew = "10" #Left-Right
            elif (self.h_step == "ONE"):
                sValueNew = "30" #Left
            elif (self.h_step == "TWO"):
                sValueNew = "40" #Middle-Left
            elif (self.h_step == "THREE"):
                sValueNew = "50" #Central
            elif (self.h_step == "FOUR"):
                sValueNew = "60" #Middle-Right
            elif (self.h_step == "FIVE"):
                sValueNew = "70" #Right
            elif (self.h_step == "LEFT_HALF"):
                sValueNew = "80" #Left-Middle
            elif (self.h_step == "RIGHT_HALF"):
                sValueNew = "90" #Middle-Right
            elif (self.h_step == "OFF"):
                sValueNew = "20" #None
                
            if (Devices[6].nValue != self.operation or Devices[6].sValue != sValueNew):
                Devices[6].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("hStep received! Current: " + self.h_step)
                
            # Swing Vertival (vStep)
            if (self.v_step == "ALL"):
                sValueNew = "10" #Up-Down
            elif (self.v_step == "OFF"):
                sValueNew = "20" #None
            elif (self.v_step == "ONE"):
                sValueNew = "30" #Top
            elif (self.v_step == "TWO"):
                sValueNew = "40" #2
            elif (self.v_step == "THREE"):
                sValueNew = "50" #3
            elif (self.v_step == "FOUR"):
                sValueNew = "60" #4
            elif (self.v_step == "FIVE"):
                sValueNew = "70" #5
            elif (self.v_step == "SIX"):
                sValueNew = "80" #Bottom
                
            if (Devices[7].nValue != self.operation or Devices[7].sValue != sValueNew):   
                Devices[7].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("vStep received! Current: " + self.v_step)
                
            # Current Power (energy.onCurrent)
            # if (Devices[8].sValue != (str(self.power) + ";0")):
                # import web_pdb; web_pdb.set_trace()
                # Devices[8].Update(nValue = self.operation, sValue = self.power + ";0")
                # Domoticz.Log("power received! Current: " + self.power)

        # AWHP part
        if Parameters["Mode1"] == "type_awhp":
            # Operation
            if (self.operation == 0):
                if (Devices[1].nValue != 0):
                    Devices[1].Update(nValue = 0, sValue ="0") 
                    Domoticz.Log("operation received! Current: " + str(self.operation))
            else:
                if (Devices[1].nValue != 1):
                    Devices[1].Update(nValue = 1, sValue ="100")
                    Domoticz.Log("operation received! Current: " + str(self.operation))
                
            # Mode (opMode)
            if (self.op_mode == "COOL"):
                sValueNew = "10" #Auto
                newImage = 16
            elif (self.op_mode == "AI"):
                sValueNew = "20" #Cool
                newImage = 16
            elif (self.op_mode == "HEAT"):
                sValueNew = "30" #Heat
                newImage = 15
                
            if(Devices[2].nValue != self.operation or Devices[2].sValue != sValueNew):
                Devices[2].Update(nValue = self.operation, sValue = sValueNew, Image = newImage)
                Domoticz.Log("Mode received! Current: " + self.op_mode)
                
            # Target temp (tempState.target)
            if (Devices[3].nValue != self.operation or Devices[3].sValue != self.target_temp):
                Devices[3].Update(nValue = self.operation, sValue = self.target_temp)
                Domoticz.Log("tempState.target received! Current: " + self.target_temp)
                
            # Hot water temp (airState.tempState.hotWaterCurrent)
            if (Devices[4].nValue != self.operation or Devices[4].sValue != self.hot_water_temp):
                Devices[4].Update(nValue = self.operation, sValue = self.hot_water_temp)
                Domoticz.Log("airState.tempState.hotWaterCurrent received! Current: " + self.hot_water_temp)
                
            # Input water temp (tempState.inWaterCurrent)
            if (Devices[5].nValue != self.operation or Devices[5].sValue != self.in_water_temp):
                Devices[5].Update(nValue = self.operation, sValue = self.in_water_temp)
                Domoticz.Log("tempState.inWaterCurrent received! Current: " + self.in_water_temp)
            
            if (Devices[7].nValue != self.operation or Devices[7].sValue != self.cur_temp):
                Devices[7].Update(nValue = self.operation, sValue = self.cur_temp)
                Domoticz.Log("airState.tempState.current received! Current: " + self.cur_temp)
			
            # Output water temp (tempState.outWaterCurrent)
            if (Devices[6].nValue != self.operation or Devices[6].sValue != self.out_water_temp):
                Devices[6].Update(nValue = self.operation, sValue = self.out_water_temp)
                Domoticz.Log("tempState.outWaterCurrent received! Current: " + self.out_water_temp)
				
            if (Devices[8].nValue != self.operation or Devices[8].sValue != self.goraca_woda):
                Devices[8].Update(nValue = self.operation, sValue = self.goraca_woda)
                Domoticz.Log("airState.tempState.current received! Current: " + self.goraca_woda)
				
            if (self.tryb_mode == "AIR"):
                sValueNew = "10" #Up-Down
            elif (self.tryb_mode == "WATER"):
                sValueNew = "20" #None

                
            if (Devices[9].nValue != self.operation or Devices[9].sValue != sValueNew):   
                Devices[9].Update(nValue = self.operation, sValue = sValueNew)
                Domoticz.Log("tryb received! Current: " + self.tryb_mode)
                
                
#            if (self.tryb_silent == "ON"):
#                sValueNew = "10" #Up-Down
#            elif (self.tryb_silent == "OFF"):
#                sValueNew = "20" #None

                
#            if (Devices[10].nValue != self.operation or Devices[10].sValue != sValueNew):   
#                Devices[10].Update(nValue = self.operation, sValue = sValueNew)
#                Domoticz.Log("tryb received! Current: " + self.tryb_silent)

            # Output water temp (tempState.outWaterCurrent)
 #           if (Devices[7].nValue != self.operation or Devices[7].sValue != self.cur_temp):
 #               Devices[7].Update(nValue = self.operation, sValue = self.cur_temp)
 #               Domoticz.Log("airState.tempState.current received! Current: " + self.cur_temp)

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()
	

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return

def DumpDictionaryToLog(theDict, Depth=""):
    if isinstance(theDict, dict):
        for x in theDict:
            if isinstance(theDict[x], dict):
                Domoticz.Log(Depth+"> Dict '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpDictionaryToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], list):
                Domoticz.Log(Depth+"> List '"+x+"' ("+str(len(theDict[x]))+"):")
                DumpListToLog(theDict[x], Depth+"---")
            elif isinstance(theDict[x], str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theDict[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theDict[x]))

def DumpListToLog(theList, Depth):
    if isinstance(theList, list):
        for x in theList:
            if isinstance(x, dict):
                Domoticz.Log(Depth+"> Dict ("+str(len(x))+"):")
                DumpDictionaryToLog(x, Depth+"---")
            elif isinstance(x, list):
                Domoticz.Log(Depth+"> List ("+str(len(theList))+"):")
                DumpListToLog(x, Depth+"---")
            elif isinstance(x, str):
                Domoticz.Log(Depth+">'" + x + "':'" + str(theList[x]) + "'")
            else:
                Domoticz.Log(Depth+">'" + x + "': " + str(theList[x]))

# Configuration Helpers
def getConfigItem(Key=None, Default={}):
    Value = Default
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Value = Config[Key] # only return requested key if there was one
        else:
            Value = Config      # return the whole configuration if no key
    except KeyError:
        Value = Default
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration read failed: '"+str(inst)+"'")
    return Value
    
def setConfigItem(Key=None, Value=None):
    Config = {}
    try:
        Config = Domoticz.Configuration()
        if (Key != None):
            Config[Key] = Value
        else:
            Config = Value  # set whole configuration if no key specified
        Config = Domoticz.Configuration(Config)
    except Exception as inst:
        Domoticz.Error("Domoticz.Configuration operation failed: '"+str(inst)+"'")
    return Config
