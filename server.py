# Copyright 2015 gRPC authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from keras.layers import Dense, BatchNormalization, Input, Dropout, Activation, concatenate, GRU, Dropout

from concurrent import futures
import logging, grpc, time
import numpy as np
import threading
  
import model_class as mc
import server_tools_pb2
import server_tools_pb2_grpc
import pandas as pd
from keras.models import Model

_ONE_DAY_IN_SECONDS = 60 * 60 * 24
PORT='50051'

global processes, max_id, results, max_client_ids, max_client_id, new_client_permitted, times
processes = {}
max_client_ids = {}
max_client_id = 0
max_id = 0
new_client_permitted = True
results = {}
times = {}

class Model4ExpLLLow(mc.ClassModel):
    def get_outputs(self):
        self.name = '4layersExpLLLow'
        RATE=0.001
        self.epochs = 11
        h = self.inputs
        h = Dropout(rate=RATE)(h)
        h = Dense(36, activation='relu')(h)
        norm = Dropout(rate=RATE)(h)
        h = Dense(11, activation = 'relu')(norm)
        norm = Dropout(rate=RATE)(h)
        h = Dense(3, activation = 'relu')(norm)
        return Dense(1, activation='linear', name='output')(h)



def verify_request(request):
    logging.info("Client id is " + str(request.client_id))
    #logging.info("Max Client id is " + str(request.max_client_ids))
    logging.info("Batch size is " + str(request.batch_size))
    return (request.client_id in max_client_ids) and request.batch_size > 0

class MnistServer(server_tools_pb2_grpc.MnistServerServicer):
    def StartJobWait(self, request, context):
        logging.info("StartJobWait begins")
        if not verify_request(request):
            logging.error("Request is invalid and failed the verification processes")
            return server_tools_pb2.PredictionMessage(complete=False, prediction=b'', error='Invalid data package', infer_time=0)
        # data = np.frombuffer(request.images)
        # data = data.reshape(-1, 28, 28, 1)
        logging.info("Request is valid and data preparation succeeds, ml prediction begins")
        sample = mc.Sample()
        sample.X = pd.read_json(request.x_input.decode('utf-8'))
        print("Type of X is", type(sample.X), sample.X.shape)
        sample.Y = pd.read_json(request.y_input.decode('utf-8'))
        print("Type of Y is", type(sample.Y), sample.Y.shape) 
        sample.X.drop(['PU','pt'],1,inplace=True)
        sample.idx = np.random.permutation(sample.X.shape[0])
        print('Standardizing...')
        mu, std = np.mean(sample.X, axis=0), np.std(sample.X, axis=0)
        sample.standardize(mu, std)
        n_inputs = sample.X.shape[1]
 
        model = Model4ExpLLLow(n_inputs, True)
        print("Model name is ",model.name)
        model.train(sample, num_epochs=32, mahi=True)

        
        #Do prediction here


        #prediction, predict_time = ml.predict(data, request.batch_size)
        prediction = "Succeed because doesn't do anything??"
        logging.info("ML prediction succeeds")
        return server_tools_pb2.PredictionMessage(complete=True, prediction=prediction.encode('utf-8'), error='', infer_time=0.12345)

    def RequestClientID(self, request, context):
        global max_client_id, new_client_permitted, max_client_ids
        while not new_client_permitted:
            pass

        new_client_permitted = False
        client_id = str(max_client_id)
        max_client_id += 1
        new_client_permitted = True

        max_client_ids[client_id] = 0
        return server_tools_pb2.IDMessage(new_id=client_id, error = '')

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server_tools_pb2_grpc.add_MnistServerServicer_to_server(MnistServer(), server)
    server.add_insecure_port('[::]:'+PORT)
    server.start()
    print("READY")
    try:
        while True:
            time.sleep(_ONE_DAY_IN_SECONDS)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':

    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    serve()