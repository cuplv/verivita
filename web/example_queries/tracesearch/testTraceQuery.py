import requests
url = 'http://localhost:9000/'


trace_search_headers = {"Content-Type" : "application/JSON"}
def testTracesSearchRank():
    local_url = url + 'traces_search/rank'
    data_file = file('two_edge_create.json','r')
    data = data_file.read()
    requests.get
    print ""
