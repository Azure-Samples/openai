### How to run the project

#### Notes:

- Make sure your **Qdrant dev tunnel is also already setup**
- Run
```
docker run -d -p 6333:6333 -p 6334:6334 -v "$pwd/qdrant_storage:/qdrant/storage:z" qdrant/qdrant
```
- An easy way to set up dev tunnels in VS code is to use the **Ports** window (next to Terminal/Output window)
	- Click on "Forward a Port" button
		- add port 6333 and 6334
		- right-click on forwarded address and set `Port Visibility` to public
		- right-click on forwarded address and `Copy Local Address` and place it in the `QdrantEndpoint` section of the `appsettings.development.json` file.

```
git clean -fdx
```

- Open **Visual Studio int preview - Run as administrator**
- **Include appsettings.development.json** for TeamsApp and GithubRepoAssistant.ApiService app if missing
- **Rebuild** all projects - (doesn't matter in debug or release) -> **prefer Release**
- Set the **Teams App as Startup** 

	- **configure dev tunnels** - maybe create new
		- Tunnel Type: Persistent
		- Access: Public
	- confirm the new **dev tunnel is selected** for the teams app
	- right click **prepare teams toolkit **
		- if fails just look at dev tunnels again and hit prepare teams toolkit again
		- (the second time should work - might just fail once after first "git clean -fdx")
		- (just know every time you open VS you would need to do the prepare teams toolkit step **at least once per VS instance**)


- right click set **apphost as startup** the 
	- hit "Debug > Start without Debugging" or **Ctrl+F5**
		- VS will show a **pop up**, saying "**there were deployment error** - do you wanna continue" 
			- just **ignore** and say yes 
			- (and maybe ignore that pop up for future)
- then you will see the ports will populate in dev tunnels as the apps get started with aspire
- check out webfrontend
- check out GithubRepoAssistant.ApiService swagger
- checkout teams 
	- just **ignore** the prefix http://localhost:5130/ from dashboard if you wanna directly click on endpoint below
	- or go to webfrontend click on the teams page - sync it with url in launchSettings.json


