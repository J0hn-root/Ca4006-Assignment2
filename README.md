Instructions to run the project

1. Run docker image
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.11-management

- user:       guest
- password:   guest

2. Install python dependencies

- python -m pip install pika --upgrade

3. run the following commands in different terminals:

    - python funding_agency.py
    - python university.py
    - python researcher.py 1
    - python researcher.py 2

    To run researcher.py an id value must be provided on the command line

    The databases for funding_agency and university are objects, and they are pickled and stored in a file.
    To delete the data delete the pickle files in the current directory.

4. run command:
    
    - python main.py

    This program allows you to interact with the researchers and send request to the university database.
    
    Multiple requests can be submitted by concatenating the commands using the pipe ('|') character:
        - '1:add:3 | 2:details | 4:transactions'