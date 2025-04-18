Installation and Deployment

Pre-requisites installations:

Python 3.9
Docker (Optional)

Pre-requisite keys:
	
OpenAI API key

Place the key in a .env file with your key at OPENAI_API_KEY in the project folder

E.X.
OPENAI_API_KEY=$key


Download all project files, and run:

	pip install -r requirements.txt


Basic Local Deployment

To deploy the basic flask API, CD to your project folder, and run the file:

	python app.py

This will open a new port on your local host at port 5000.

To test the open port, use postman or console commands to form a request. For ease of testing, I made a new Powershell terminal and used:

Invoke-WebRequest -Uri http://localhost:5000/conversations -Method Post

This creates a session ID that you can then continue the conversation, by using the following command and replacing the uuid with the session ID:

Invoke-WebRequest -Uri http://localhost:5000/conversations/{uuid}/messages -Method Post -Body '{"message": "I want to cancel my order 12345"}' -ContentType "application/json"


![Screenshot 2025-03-18 090707](https://github.com/user-attachments/assets/3d96f03c-2fa3-4025-98a3-afb977ee11f8)





Robust Deployment

The project also comes will everything needed to run the project as a containerized solution. Once you have Docker downloaded and running, CD to your project folder, and run:

docker-compose build

Wait for all messages to pass, then run:

docker-compose up

This will start your container and the port will be open. From here the testing instructions are the same as the Flask API, and without further configuration can still be tested using:

Invoke-WebRequest -Uri http://localhost:5000/conversations -Method Post

Invoke-WebRequest -Uri http://localhost:5000/conversations/{uuid}/messages -Method Post -Body '{"message": "I want to cancel my order 12345"}' -ContentType "application/json"



Solution Details

The core of this solution revolves around utilizing ChatGPT as a classifier to identify the core need of the user. Given that this is a task-oriented bot, I needed to ensure that GPT would supply a consistently formatted solution that I could use in conditional logic for the lookups. I accomplished this by using OpenAI’s new structured formatting output for APIs (at the cost of using a newer model), and prompt engineering to provide the scope of the taxonomy and example output JSONs.

The solution is currently limited in that it needs the ID in the user request to work properly. And it doesn’t handle follow-up questions well because I didn’t bounce details from the CSV into the Prompt. Though this could be trivially resolved by adding in a new field in the UttClassification for the item name, and allowing GPT to fill N/A when either the name or ID is not given.
