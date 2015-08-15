import socket
import StringIO
import sys

class WSGIServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # creating a listen socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )

        # reuse socket if in time wait set by previous process
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        #binding to host, port of server
        listen_socket.bind(server_address)

        #backlog of incoming requests
        listen_socket.listen(self.request_queue_size)
       
        #host, port of the server in which this socket is listening
        host, port = self.listen_socket.getsockname()[:2]
        
        #gets domain name of the host
        self.server_name = socket.getfqdn(host)
        self.server_port = port

        #Return headers set by Web framework/Web application
        self.headers_set = []

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket

        while True:
            # new client connection
            self.client_connection, client_address = listen_socket.accept()
            self.handle_one_request()
            # loop over to another connection

    def handle_one_request(self):
        self.request_data = request_data = self.client_connection.recv(1024)
        
        # printing the request data
        print (''.join('< %s\n' % s for s in request_data.splitlines()))
        
        #parse the request 
        self.parse_request(request_data)
        
        #create environment to be passed to the application
        env = self.get_environ()

        #call the application and get result for the url
        result = self.application(env, self.start_response)
        
        # Construct a response and send it back to the client
        self.finish_response(result)

    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.strip('\r\n')


        #set class parameters
        (self.request_method,
         self.path,
         self.request_version
         ) = request_line.split()
        
    def get_environ(self):
        ''' this return a event dictionary to be used
        by the application to know details about the wsgi server
        and the http request
        '''
        env = {}

        #setting up wsgi protocol variables
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        env['wsgi.input'] = StringIO.StringIO(self.request_data)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multiprocess'] = False
        env['wsgi.multithread'] = False
        env['wsgi.run_once'] = False

        #required request variables
        env['REQUEST_METHOD'] = self.request_method
        env['PATH_INFO'] = self.path
        env['SERVER_NAME'] = self.server_name
        env['SERVER_PORT'] = str(self.server_port)
        return env

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [
            ('Date', 'Sat, 15 Aug 2015, 11:31:31 GMT+0530'),
            ('Server', 'WSGIServer 0.2')
         ]
        
        #complete header set
        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status} \r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)

            response += '\r\n'

            for data in result:
                response += data

            print (''.join('> {line}\n'.format(line=line)
                            for line in response.splitlines())
                   )

            self.client_connection.sendall(response)
        finally:
            self.client_connection.close()

SERVER_ADDRESS = (HOST, PORT) = '', 8888

def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print 'WSGISERVER: serving http on port %s \n' % PORT
    httpd.serve_forever()
        
        
        
