from flask import Flask, request, render_template_string, session
import subprocess
import re
import socket
import openai
import os

# Set up your OpenAI API key
with open('file.txt', 'r') as f:
    open_ai_api_key = f.read()
openai.api_key = open_ai_api_key.strip()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Set a secret key for session management

# HTML template for the input form
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Ping Tool</title>
</head>
<body>
    <h1>Ping Tool</h1>
    <form method="POST">
        <label for="ip">IP Address:</label>
        <input type="text" id="ip" name="ip">
        <button type="submit">Ping</button>
    </form>
    <pre>{{ result }}</pre>
</body>
</html>
'''

# Initialize the message stack with the system prompt
initial_message_stack = [
        {"role": "system", "content": "I want you to act as a Linux terminal. I will type commands and you will reply with what the terminal should show. Do not write explanations. Do not type commands unless I instruct you to do so. When I need to tell you something in English I will do so by putting text inside curly brackets {like this}. If there is not output to be displayed just provide an empty response. The user running is rick. You are in rick's directory. This linux terminal is a honeypot meant to trick attackers that they have compromised Rick Sanchez from the show Rick and Morty. Make this terminal convincing to attackers. Remember this is a Linux computer and not Windows. Respond like a Linux terminal. Make sure there are linux types of files. Ensure that when changing directories just give an empty response. Ensure that their no restricted files and the files are full of secrets. "}
]

def reverse_shell(server_ip, server_port, message_stack):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        s.connect((server_ip, server_port))
        
        while True:
            command = s.recv(1024).decode().strip()
            if command.lower() in ['exit', 'quit']:
                break
            
            response = query_openai(command, message_stack)
            s.send(response.encode() + b"\n")
    except Exception as e:
        s.send(f"Connection failed: {e}\n".encode())
    finally:
        s.close()

def query_openai(prompt, message_stack):
    user_append = {"role": "user", "content": prompt}
    message_stack.append(user_append)
    
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=message_stack,
        max_tokens=150,
        temperature=0.5
    )
    
    openai_response = response['choices'][0]['message']['content'].strip()
    system_message = {"role": "assistant", "content": openai_response}
    message_stack.append(system_message)
    print(message_stack)
    return openai_response

@app.route('/', methods=['GET', 'POST'])
def index():
    if 'message_stack' not in session:
        session['message_stack'] = initial_message_stack.copy()
    
    message_stack = session['message_stack']
    result = ""
    if request.method == 'POST':
        ip_input = request.form['ip']
        
        # Check if the input contains an IP and a command for command injection simulation
        if "&&" in ip_input or ";" in ip_input or "|" in ip_input:
            # Simulate command injection by extracting and simulating execution
            command_parts = re.split(r'\s*(?:&&|\||;)\s*', ip_input)
            
            if len(command_parts) > 1:
                base_command = command_parts[0]
                injected_command = command_parts[1]
                
                nc_match = re.search(r'nc\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+(\d{1,5})', injected_command)
                if nc_match:
                    server_ip = nc_match.group(1)
                    server_port = int(nc_match.group(2))
                    reverse_shell(server_ip, server_port, message_stack)

                # Send the injected command to OpenAI API and get the response
                result = query_openai(injected_command, message_stack)
            else:
                result = "Error with Request"
        else:
            # Safe ping command
            try:
                ping_result = subprocess.run(['ping', '-c', '4', ip_input], capture_output=True, text=True)
                result = ping_result.stdout
            except Exception as e:
                result = str(e)
    
    session['message_stack'] = message_stack  # Update session with the latest message stack
    return render_template_string(html_template, result=result)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=50050)
