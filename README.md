# OAR - Online Research Assistant

----------> TODO <-----------
- Copy abstract from proposal here
- After abstract - mention that it collects feedback from users
- Add proposal document to the documentation folder
----------> /TODO <-----------

## Architecture

![Architecture](./documentation/architecture.png)

## Components
Standard Backend/UI/DB components which are uploaded to the cloud (AWS) for serving.

### UI
Web user interfaces which interacts with the user and upon conversation, discovers domain of interest or exposes the user to new ones. After understanding the domain of interest, displays relevant articles while extracting specific information, such as abstract, keywords (if available), future work and conclusions. 

The UI is partially responsive, build with HTML 5.0, CSS 3.0 and JS.
### Backend
Restful Backend service which exposes 2 endpoints, one for the conversation (ask) and the other for the training (train). The backend also utilizes multiprocessing for true CPU utilization.

#### Send a new message

```http
  POST /ask
```

| Parameter     | Type     | Description                         |
| :------------ | :------- | :---------------------------------- |
| `messageText` | `string` | **Required**. message from the user |

#### Send a new message

```http
  GET /train
```

The Backend is built with Python and Flask as the backbone.

After calling train, run the following SQL query:
```SQL
INSERT INTO statement 

SELECT NULL, text, search_text, conversation, created_at, in_response_to, search_text as serach_in_response_to, persona FROM statement where text like '%Here are the following sub-domains:%'
```

### DB
Naive file based on a database using SQLite. 
#### Tables
* articles - table containing history searches of articles
* tag_association

## Deployment
- AWS

## Continuous Learning
- Feedback from the users for usage purposes. 
- Constantly training the model with changing fields

## Project Structure
### Package UML
![Hierarchy](./documentation/packages.png)
### Classes UML
![Hierarchy](./documentation/classes.png)

## Running Locally
Prerequisites:
- Python 3.7 
- [BuildTools] in case you are on windows

### Windows
1. Install python 
2. Creating a virtual environment
```powershell
  python -m venv .venv37
  source ~/OAR/.venv37/bin/activate
  python --version #verify that you are running with venv python
```
3. install dependencies
```powershell
  pip install -r ./requirements.txt
  python -m spacy download en # *possible error - run python as an administrator* 
```
4. Run backend
```powershell
  python /oar.py
```
5. Open browser and navigate to localhost:5000
6. host also pydoc for documentation
```powershell
  python -m pydoc -b
```

### Linux/MacOS
1. Installing python
2. Creating a virtual environment
```bash
  python -m venv .venv37
  source ~/OAR/.venv37/bin/activate
  which python #verify that you are running with venv python 
```
3. install dependencies
```bash
  pip install numpy==1.19.0
  export -u MACOSX_DEPLOYMENT_TARGET=11.5
  pip install -r ./requirements.txt
  python -m spacy download en
```
4. Run backend
```bash
  python /oar.py
```
5. Open browser and navigate to localhost:5000
6. host also pydoc for documentation
```bash
  python -m pydoc -b
```

## Future Work
### Engines
- Recommendation engine
- RL engine based on previous search results and successes (if the user clicked on an article)
- Add more engines
- - https://www.osti.gov/dataexplorer/search/product-type:Dataset/semantic:cat
- - https://www.science.gov/scigov/desktop/en/results.html
- - https://www.semanticscholar.org/search?q=cat&sort=relevance
### Infrastructure
- Migrate SQLite to Postgres
- Automate field training
- Discover new fields based on user searches

[BuildTools]: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2019
