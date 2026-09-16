#!/usr/bin/env python3
import argparse
import json
from pprint import pprint

from redash_toolbelt.client import Redash

template = """/*
Name: {name}
Data source: {data_source}
Created By: {created_by}
Last Updated At: {last_updated_at}
*/
{query}"""


def build_opts(opt_dict):
    """build out minimal options"""
    options = {}
    for subopt in ['globalSeriesType', 'sortX', 'legend', 'yAxis', 'xAxis', 'series', 'seriesOptions', 'columnMapping', 'bottomMargin']: 
        if subopt in opt_dict:
            options[subopt] = opt_dict[subopt]
    return options


def save_dashboards(redash_h, url, api_key, condense):
    for dash in redash_h.paginate(redash_h.dashboards):
        filename = f"dashboard_{dash['id']}.json"
        d2 = redash_h.get_dashboard(dash['id'])
        if condense:
            print(filename)
            condensed = []
            # special widget
            if len(d2['widgets']) == 0:
                # empty
                continue
            w = d2['widgets'][0]
            if 'visualization' in w:
                tdict = {}
                for k in ['description', 'name']:
                    if k in w['visualization']:
                        tdict[k] = w['visualization'][k]
                    if k in w['visualization']['query']:
                        tdict[k] = w['visualization']['query'][k]
                    if 'schedule' in w['visualization']['query'] and isinstance(w['visualization']['query']['schedule'], dict):
                        if 'interval' in w['visualization']['query']['schedule']:
                            tdict['schedule'] = w['visualization']['query']['schedule']['interval']
                condensed.append(tdict)
            for w in d2['widgets'][1:]:
                tdict = {}
                if 'visualization' not in w:
                    continue
                for k, v in w['visualization'].items():
                    viz = {}
                    if k in ['type', 'description', 'name'] and ((isinstance(v,dict) and v != {}) or (isinstance(v,str) and v != "")):
                         viz[k] = v
                            
                    if k == "options":
                        viz['options'] = build_opts(v)
                    # take options from query if we don't have an upper level options
                    if k == "query" and 'options' not in viz:
                        if "options" in v:
                            if "options" not in viz:
                                viz['options'] = build_opts(v['options'])
                            else:
                                viz['options'].update(build_opts(v['options']))
                    if viz != {}:
                        if 'visualization' not in tdict:
                            tdict['visualization'] = {}
                        tdict['visualization'].update(viz)

                if tdict != {}:
                    condensed.append(tdict)

            # reassign
            # d2 = condensed
            pprint(condensed)
            
        with open(filename, 'w') as f:
            f.write(json.dumps(d2, indent=4))


def main():
    parser = argparse.ArgumentParser(description="dump out dashboards in json format")

    parser.add_argument("--redash-url", required=True)
    parser.add_argument("--api-key", required=True, help="api key for redash")
    parser.add_argument("--condense", action="store_true", required=False, default=False, help="condense to get visualization and options without full query")
    args = parser.parse_args()

    redash_h = Redash(args.redash_url, args.api_key)

    # pprint(dashes, indent=4)
    save_dashboards(redash_h, args.redash_url, args.api_key, args.condense)


if __name__ == '__main__':
    main()
