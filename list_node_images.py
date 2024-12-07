#!/usr/bin/python
# Usage: kubectl get node [optional: name of node] -o json | python list_node_images.py
import sys
import json
data = json.load(sys.stdin)
# try:
#     nodes = data['items']
# except KeyError:
#     nodes = [data]
# for node in nodes:
#     node_name = node['metadata']['name']
#     print("\nNODE {}".format(node_name))
#     print("REPOSITORY".ljust(48) +"  "+ "TAG".ljust(16) +"  "+ "SIZE")
#     images = node['status']['images']
#     for image in images:
#         if len(image['names'])<2:
#             continue
#         names = image['names'][1].rsplit(":",1)
#         name = names[0]
#         tag = names[1]
#         size = image['sizeBytes']
#         size_mb = "{0:.1f}MB".format(size/1000000.)
#         print(name.ljust(48) +"  "+ tag.ljust(16) +"  "+ size_mb)



node = data
images = node['status']['images']

images_list = []

for image in images:
    if len(image['names'])<2:
        continue
    full_image = image['names'][1].rsplit(":",1)
    size = image['sizeBytes']
    next_image = {
        'name' : full_image[0],
        'tag' : full_image[1],
        'size_mb' : "{0:.1f}".format(size/1000000.)
    }
    images_list.append(next_image)
print(images_list)
