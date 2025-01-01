:: https://hackmd.io/@peterju/B1pUqd-5c
@echo off

set argNum=0
for %%x in (%*) do (
	set /A argNum+=1
)

echo %argNum%

for %%x in (%*) do (
	echo %%x
	start cmd /k "py .\HciSnoop_Tester_3.3.py %%x"

)
:: start cmd /k "py .\HciSnoop_Tester_3.1.py %1"
:: start cmd /k "py .\HciSnoop_Tester_3.1.py %2"


:: py .\HciSnoop_Tester_3.1.py .\WSW26786_LlDdiScnBv19C_DEV1.txt
:: py .\HciSnoop_Tester_3.1.py .\WSW26786_LlDdiScnBv19C_DEV2.txt
