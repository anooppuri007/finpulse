import urllib.request
import json

def test_dbnomics():
    # US CPI from OECD
    url = "https://api.db.nomics.world/v22/series/OECD/MEI/USA.CPALTT01.IXOB.M?limit=1"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        res = urllib.request.urlopen(req)
        data = json.loads(res.read())
        doc = data['series']['docs'][0]
        # values are in doc['value'], but it might be 'values' or a list of pairs
        print("OECD USA CPI keys:", doc.keys())
        if 'value' in doc:
            print("Value array:", doc['value'][:5])
            print("Period array:", doc['period'][:5])
    except Exception as e:
        print("DBNomics error:", e)

test_dbnomics()
