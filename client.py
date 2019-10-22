import logging
import grpc
import time
import numpy as np
import pandas as pd
import server_tools_pb2
import server_tools_pb2_grpc
from google.protobuf import empty_pb2

PORT = '50051'
VALSPLIT = 0.2
np.random.seed(5)
Nrhs = 500000


def run_facile(host_IP):
    # Get a handle to the server
    options = [('grpc.max_receive_message_length', 500*1024*1024 )]
    #print("Max message length is ", grpc.max_message_length)
    channel = grpc.insecure_channel(host_IP + ':' + PORT, options = options)
    stub = server_tools_pb2_grpc.MnistServerStub(channel)

    # Get a client ID which you need to talk to the server
    try:
        logging.info("Request client id from server")
        response = stub.RequestClientID(server_tools_pb2.NullParam())
    except BaseException:
        print(
             """Connection to the server could not be established.
             Press enter to try again.""")
        return
    client_id = response.new_id
    logging.info("Client id is " + str(client_id))

    X = pd.read_pickle("input/X_HB.pkl")[:Nrhs]
    Y = pd.read_pickle("input/Y_HB.pkl")[:Nrhs]

    x_input = X.to_json().encode('utf-8')
    y_input = Y.to_json().encode('utf-8')

    # Send the data to the server and receive an answer
    start_time = time.time()
    logging.info("Number tested is " + str(Nrhs))
    logging.info("Submitting files and waiting")
    data_message = server_tools_pb2.DataMessage(
        client_id=client_id, x_input=x_input, y_input=y_input, batch_size=32)
    response = stub.StartJobWait(data_message, 100, [])

    # Print output
    whole_time = time.time() - start_time
    print("Predict time:", response.infer_time)
    print("Fraction of time spent not predicting:",
          (1 - response.infer_time / whole_time) * 100, '%')
    #print(response.prediction)
    #print(np.frombuffer(response.prediction,dtype = np.float32))
    channel.close()


if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--IP', type=str, default="localhost")
    args = parser.parse_args()
    logging.basicConfig()
    logging.root.setLevel(logging.NOTSET)
    logging.basicConfig(level=logging.NOTSET)
    for i in range(20):
        run_facile(args.IP)
