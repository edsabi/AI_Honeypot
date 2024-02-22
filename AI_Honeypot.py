import re
from flask import Flask, render_template, request
import socket
import requests
import json
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        input_text = request.form.get('input_field')
        ip_addresses = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', input_text)
        ports = re.findall(r'(?<=\d\s)\d{1,5}(?!\.)', input_text)
        ports = [port for port in ports if int(port) <= 65535]
        #return f"IP Addresses: {ip_addresses[0]}<br>Ports: {ports[0]}"
        print('connecting')
        HOST = ip_addresses[0]
        PORT = ports[0]
        print(HOST)
        print(PORT)
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, int(PORT)))
        with open('file.txt','r') as f:
            blah=f.read()
        url = 'https://api.openai.com/v1/chat/completions'
        headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+blah.rstrip()}
        message_stack = [
                {"role": "system", "content": "ChatGPT, pretend you are a Linux terminal. Respond to my inputs as if they are Linux commands. Handle common commands (ls, cd, cat, etc.) and simulate a file system. If I enter an incorrect command, show typical Linux error messages. You can also simulate advanced features like pipes, redirection, and simple scripts. Remember Linux Commands only. Do not respond as if you were a Windows Terminal.Do not type sentences to me. Respond as if you were a linux terminal"}
        ]
        while True:
            command = s.recv(1024).decode()
            message= f"Respond to the command,{command}, as linux terminal should"
            user_message = {"role":"user", "content": command}
            message_stack.append(user_message)
            data = {
                "model": "gpt-3.5-turbo",
                "temperature": 0,
                "max_tokens": 521,
                "top_p": 0.1,
                "frequency_penalty":-0.2,
                "presence_penalty":-0.2,
                "messages": message_stack
            }
            response = requests.post(url, headers=headers, json=data, verify=False)
            data = json.loads(response.text)
            try:   
                response_message = data['choices'][0]['message']['content']
                formatted_response = response_message.replace("\n", "\n ")
                print( formatted_response)
                s.send(bytes(formatted_response+'\n','utf-8'))
                system_message = {"role": "system", "content": response_message}
                message_stack.append(system_message)
            except Exception as e:
                print(response.text)

        s.close()
        return f"IP Addresses: {ip_addresses[0]}<br>Ports: {ports[0]}"
    return render_template('index.html')    
if __name__ == "__main__":
    app.run(host= '0.0.0.0',port=50050) 
