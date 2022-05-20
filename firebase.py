# import os
# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import storage
# from firebase_admin import firestore

# cred_file_path = ""

# tmp_cred_file_path = "tmp/cred.json"

# is_local = os.path.exists("cert.json")

# if is_local:
#     cred_file_path = "cert.json"
# else:
#     json = os.environ.get("cert_json")
#     with open(tmp_cred_file_path, mode='w') as f:
#         f.write(json)
#     cred_file_path = tmp_cred_file_path

# from google.oauth2 import service_account

# cred = credentials.Certificate(cred_file_path)

# if not is_local:
#     os.remove(tmp_cred_file_path)

# firebase_app = firebase_admin.initialize_app(cred, {
#     'storageBucket': 'word-detective-7ac3b.appspot.com',
#     'projectId': 'word-detective-7ac3b',
# })


# bucket = storage.bucket()

# db = firestore.client()

import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
from firebase_admin import firestore

cred_file_path = "cred.json"
cert_json_str = os.environ.get("cert_json")
print(cert_json_str)

f = open(cred_file_path, mode='w')
f.write(cert_json_str)
f.close()
cred = credentials.Certificate(cred_file_path)
print("test")
# os.remove(cred_file_path)

firebase_app = firebase_admin.initialize_app(cred, {
    'storageBucket': 'word-detective-7ac3b.appspot.com',
    'projectId': 'word-detective-7ac3b',
})

bucket = storage.bucket()

db = firestore.client()
