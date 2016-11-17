from flask import Flask
from flask import jsonify
from flask import make_response
from flask import abort
from flask import request
import requests
import json
import uuid
import sys

app = Flask(__name__)

# The dictionary below, named "api_methods", lists the various URL paths that are
# available in the Flask API.

api_methods = {
    '/' : 'Your current location.',
    '/status'  : 'Displays the status of the API.',
    '/plugins' : 'Displays a list of the registered plug-ins.',
    '/task' : 'Task operations. '
}

# The dictionrary below, named "registred_plugins", may be used to list
# all of the available plugins within the AIC Framework. In the future, we should
# consider developing a framework for registering additional plugins.
# The "nxapi" plugin is used primalry to test the NX-API.
# In the intial release of the AIC Framework, only the "hba_swap" plugin will be used.

registered_plugins = {
    'hba_swap' : 'HBA Swap is used to...',
    'nxapi'   : 'Shim for NX-API tetsing.'
}

# The dictionary below, named "credentials", could be used for storing the credentials
# the App will need to access the MDS and other network devices.
# As of 11-17-16, the credentials below aren't used by Dan's "zone.py" code.

credentials = [
    {
        'ip_address': '123.34.34.12', 
        'usename': 'mike',
        'password': 'blah'
    }
]

# The array below, named "tasks", is used to store information related to the tasks
# that have been submitted to the API.
#
# The array is initilized below with no data.  The array will contain dictonaries,
# each of which will contain at a minimum: ip_address & selected-plugin. It will 
# likley also contain the status of the task. 

tasks = [
]

# The fucntion below is used to route the submitted task to the correct plugin.
# The function takes two paramters: "plugin" and "ip_address".
#
# As of 11-16-16 the "plugin" parameter must be either: "hba_swap" or "nxapi".
# For now, the code includes DEBUG output that is written to stdout. 

def call_selected_plugin(plugin, ip_address):
    sys.stdout.write('DEBUG: call_selected_plugin(): Plugin requested is "'+plugin+'".\n')
    if plugin == 'hba_swap':
        sys.stdout.write('DEBUG: call_selected_plugin(): Calling hba_swap().\n')
        hba_swap(ip_address)
    else:
        sys.stdout.write('DEBUG: call_selected_plugin(): Calling call_nxaip().\n')
        call_nxapi(ip_address)
    return 

# The function below named "hba_swap" is used to invoke thet HBA SWAP workflow. 
# This function will likley be removed or refactored to call Dan's code in 
# the "zone.py" file.
#
# This function includes DEBUG output that is written to stdout.
# The "payload" dictionray defined in the fucntion includes the parameters required 
# by the NX-API.
# 
# The fucntion also calls the "call_nxapi" fucntion with the "ipaddress" and "payload" 
# variables.

def hba_swap(ipaddress):
    sys.stdout.write('DEBUG: hba_swap(): Executing "hba_swap" plugin.\n')

    payload={
        "ins_api": {
        "version": "1.2",
        "type": "cli_show",
        "chunk": "0",
        "sid": "1",
        "input": "show zoneset active vsan 10",
        "output_format": "json"
        }
    }

    sys.stdout.write('DEBUG: hba_swap(): Calling call_nxapi().\n')
    call_nxapi(ipaddress, payload)
    return

# The function below, named "call_nxapi", is used to access the NX-API. 
# This function will likley refactored to call Dan's code in 
# the "zone.py" file.
#
# This function includes DEBUG output that is written to stdout.
# 
# For now, the MDS credeintals are defined in the variables: "switchuser" & 
# "switchpassword".
#
# The URL variable is used to build the base NX-API URL.
# This function returns the JSON response recived from the NX-API.


def call_nxapi(ip_address, payload):
    sys.stdout.write('DEBUG: call_nxapi: Executing "nxapi" plugin\n')

    switchuser='danwms'
    switchpassword='AICteam'

    url = 'http://'+ip_address+':8080/ins'
    headers = {'content-Type': 'application/json'
                }
    sys.stdout.write('DEBUG: call_nxapi(): Making NX-API Call:'+url+'\n')
    response = requests.post(url,data=json.dumps(payload), headers=headers,auth=(switchuser,switchpassword)).json()
    sys.stdout.write('DEBUG: call_nxapi(): NX-API response: '+json.dumps(response, indent=4, sort_keys=True)+'.\n')
    return response

@app.route('/')
def get_http_root():
    return 'Automated Infrastrucutre Configuration Framework v1.0'

@app.route('/aic/api/v1.0/', methods=['GET'])
def get_api_root():
    return jsonify(api_methods)

@app.route('/aic/api/v1.0/status', methods=['GET'])
def get_api_status():
    return jsonify(Status=app_status)

@app.route('/aic/api/v1.0/plugins', methods=['GET'])
def get_api_plugins_list():
    return jsonify(registered_plugins)

@app.route('/aic/api/v1.0/task', methods=['GET'])
def get_api_tasks():
    return jsonify({'task': task})

@app.route('/aic/api/v1.0/task', methods=['POST'])
def create_task():
    if not request.json or not 'ip_address' or not 'selected-task' in request.json:
        abort(400)
    if tasks:
        task_id = tasks[-1]['id'] + 1
    else:
        task_id = 1
    task = {
        'id': task_id,
        'ip_address': request.json['ip_address'],
        'selected-task': request.json.get('selected-task'),
        'done': False
    }
    tasks.append(task)
    sys.stdout.write('DEBUG: create_task(): Added task id: '+str(task_id)+' to tasks array.\n')
    sys.stdout.write('DEBUG: create_task(): Requested plugin is: '+task['selected-task']+' \n')
    sys.stdout.write('DEBUG: create_task(): Host IP Address is: '+task['ip_address']+' \n')
    sys.stdout.write('DEBUG: create_task(): Passing plugin and IP address to call_selected_plugin().\n')
    call_selected_plugin(task['selected-task'], task['ip_address'])
    
#    for task in tasks:
#    #            print task['id']
#        sys.stdout.write('For: '+str(task['id'])+' in the Tasks array:\n')
#        sys.stdout.write('The chosen plugin was: '+task['selected-task']+'\n')
#    #            print task['selected-task']
#        call_selected_plugin(task['selected-task'], task['ip_address'])
    task['done'] = True
    return jsonify({'task': task}), 201

@app.route('/aic/api/v1.0/task/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = [task for task in tasks if task['id'] == task_id]
    if len(task) == 0:
        abort(404)
    return jsonify({'task': task[0]})

@app.route('/aic/api/v1.0/plugins/nx-api', methods=['POST'])
def post_api_plugins_nxapi():
    return jsonify()

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad Request'}), 400)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

