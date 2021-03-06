# -*- coding: latin1 -*-
# $Id: CNCPendant.py,v 1.3 2014/10/15 15:04:48 bnv Exp bnv $
#
# Author:	Vasilis.Vlachoudis@cern.ch
# Date:	06-Oct-2014

__author__ = "Vasilis Vlachoudis"
__email__  = "Vasilis.Vlachoudis@cern.ch"

import os
import sys
#import cgi
import json
import urlparse
import threading
try:
	import BaseHTTPServer as HTTPServer
except ImportError:
	import http.server as HTTPServer

HOSTNAME = "localhost"
PORT = 8080

httpd = None
prgpath = os.path.abspath(os.path.dirname(sys.argv[0]))

#==============================================================================
# Simple Pendant controller for CNC
#==============================================================================
class Pendant(HTTPServer.BaseHTTPRequestHandler):
	#----------------------------------------------------------------------
	def log_message(self, fmt, *args):
		# Only requests to the main page log them, all other ignore
		if args[0].startswith("GET / "):
			HTTPServer.BaseHTTPRequestHandler.log_message(self, fmt, *args)

	#----------------------------------------------------------------------
	def do_HEAD(self, rc=200, content="text/html"):
		self.send_response(rc)
		self.send_header("Content-type", content)
		self.end_headers()

	#----------------------------------------------------------------------
	def do_GET(self):
		"""Respond to a GET request."""
		if "?" in self.path:
			page,arg = self.path.split("?",1)
			arg = dict(urlparse.parse_qsl(arg))
		else:
			page = self.path
			arg = None

		#print self.path,type(self.path)
		#print page
		#print arg

		if page == "/send":
			if arg is None: return
			for key,value in arg.items():
				if key=="gcode":
					httpd.app.queue.put(value+"\n")
				elif key=="cmd":
					httpd.app.pendant.put(value)

		elif page == "/state":
			self.do_HEAD(200, "text/text")
			self.wfile.write(json.dumps(httpd.app._pos))

		elif page == "/icon":
			if arg is None: return
			self.do_HEAD(200, "image/gif")

			filename = os.path.join(
					os.path.abspath(
						os.path.dirname(sys.argv[0])),
					"icons",
					arg["name"]+".gif")
			try:
				f = open(filename,"rb")
				self.wfile.write(f.read())
				f.close()
			except:
				pass

		else:
			self.mainPage(page)

	# ---------------------------------------------------------------------
	def mainPage(self, page):
		global prgpath
		self.do_HEAD()
		if page == "/": page = "index.html"
		try:
			f = open(os.path.join(prgpath,page),"r")
			self.wfile.write(f.read())
			f.close()
		except IOError:
			self.wfile.write("""<!DOCTYPE html>
<html>
<head>
<title>Errortitle</title>
<meta name="viewport" content="width=device-width,initial-scale=1, user-scalable=yes" />
</head>
<body>
index.html page not found.
</body>
</html>
""")

# -----------------------------------------------------------------------------
def _server(app):
	global httpd
	server_class = HTTPServer.HTTPServer
	httpd = server_class(('', PORT), Pendant)
	httpd.app = app
	try:
		httpd.serve_forever()
	except:
		httpd = None

# -----------------------------------------------------------------------------
def start(app):
	global httpd

	if httpd is not None: return False
	thread = threading.Thread(target=_server, args=(app,))
	thread.start()
	return True

# -----------------------------------------------------------------------------
def stop():
	global httpd
	if httpd is None: return False
	httpd.shutdown()
	httpd = None
	return True

if __name__ == '__main__':
	start()
