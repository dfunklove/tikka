# tikka
Tikka is a web application providing real time price updates on financial data such as stocks, currencies and cryptocurrencies.

## How does Tikka work?
The app consists of a client and server.  The server side is a Python app which retrieves data from FinnHub and serves it over a Websocket API. The client is Javascript/HTML.

## Who uses Tikka?
This app would be most useful for someone who needs to follow a single financial asset with accuracy down to the second.

## What is the goal of this project?
I created this project to demonstrate the use of Websockets in Python.  It could provide a starting point for a more complex app with features like price alerts.

## How to install
### Client
The web client expects the server app to be running on the same host.  These instructions assume you already have a running http server such as Nnginx or Apache.

This project uses Jekyll to integrate with the layout of my portfolio-site project.  It includes a default layout for use outside the portfolio.  To run the build:
1. cd into www/documents and run 'jekyll build'.  The output will appear in the \_site folder.  
2. Copy the contents of the \_site folder to a location where it can be served by your http server.

### Server
To install the server app, clone the repository onto your web server and run the following commands.
```
cd <project directory>
python setup.py bdist_wheel
pip install dist/tikka-1.0-py3-none-any.whl
tikka_server.py
```
> Note: Because it provides a secure connection, the app will need access to the certificate and private key files on your web server.  This may require changing permissions on those files.

### API Key
The server app requires a FinnHub API key in order to run.  This can be given via the command line argument '-a' or a file.  The file must be named 'config.ini' and use the format shown below.
```
[DEFAULT]
API_KEY = X
```
The file must be stored in the folder where the Tikka Python package was installed.  For the location of this folder, type 'pip show tikka'.  This gives the location where all Python packages are stored.  You must add '/tikka' to the end to get the location of the tikka package itself.  This is where you would place the file.

### Websocket Proxy
Because this project uses websockets, you must setup a websocket proxy on your http server.  Each server does this differently.  I use Nginx and have provided instructions below.

#### Nginx Configuration
The project includes a sample Nginx configuration file in the nginx_conf folder.
- If you have a working Nginx conf file, copy the end of the sample, the lines after the comment 'websocket proxy' but excluding the final '}', into the server block in your own conf file.
- If you are setting up Nginx from scratch, you can use the sample file as your default configuration.  Fill in your domain and the locations of your certificate and key files, and copy the file to the conf.d folder in your Nginx installation.

## Running the Application
Open the web client in your web browser.  The location will depend on where you stored the files under the document root.  If you stored them in a folder called 'tikka', you would navigate to 'https://YOUR-DOMAIN/tikka'

Start typing and the autocomplete should provide a list of financial symbols that match.  Select one and click 'GO'.  The graph will say "Waiting for data."  It may take a few seconds for the graph to populate.  This is because at least two data points are required to make a graph.  If you are using the app outside of trading hours, there may not be any price updates to show.  Eventually the graph will time out and say "No data available."

If the app does not behave as expected, the web console should provide some clues as to what is going on.  If you're not using Nginx as your server, the websocket proxy is a good place to start looking for errors.

## Updating the List of Symbols
The list of symbols is stored in the file symbol_list.json in the www folder.  The autocomplete function of the web page reads from this file to give suggestions.  If you wish to update the list, follow the steps below.

1. Download three lists from FinnHub: Stock Company Symbols, Forex Symbols, and Crypto Symbols.   Links can be found the the FinnHub API documentation.
2. Remove the '[' and ']' characters from the beginning and end of each file.
3. Concactenate the three files into one big file.
4. Add one '[' at the beginning and one ']' at the end to make a single JSON array.
5. Copy the file to the environment where you installed the server app, anywhere you are able to run tikka_server.py.
6. Run this command:
    transform.py [input_file] > symbol_list.json
7. Copy symbol_list.json to the folder where you stored the tikka web app.  Look for the old symbol_list.json and replace it with the new file.

That's it!  Your symbol list is now up to date.

I've tried to cover all of the basic information needed to run the app.  If you've got questions or feedback, I'd love to hear from you!  Open an issue and I'll respond as soon as I can.  Happy trading!