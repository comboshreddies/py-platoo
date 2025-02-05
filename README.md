
# test case
philosophy

# whishlist:
- more tests
- pagination - work just in front/js payload
- database migration tool/library so db layout can be tracked

# TODO:
- pack into docker
- pack into k8s-deployment
- pack into helm
- cross connect gcp secrets/api-keys with gitlab
- terraform run GKS
- helm deploy
- github automations (gke, and local build runs)

 
# installation, setup instructions:

run:
``` console
  python3 -m venv venv
  source venv/bin/activate
  pip3 install poetry
  poetry install --without=dev
```

check PG_CONNECT of a script ./hypercorn_run.sh so it fits your postgresql settings

run:
``` console
./hypercorn_run.sh
```

