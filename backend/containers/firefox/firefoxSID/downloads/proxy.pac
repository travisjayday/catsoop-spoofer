function FindProxyForURL(url, host) {
  host = host.toLowerCase();
  if (dnsDomainIs(host, "idp.mit.edu") ||
      dnsDomainIs(host, "api-18611828.duosecurity.com") ||
	  dnsDomainIs(host, "duosecurity.com"))
    //return "PROXY 45.77.157.28:8080"; // (IP:port)
	return "DIRECT";

  return "DIRECT";
}
