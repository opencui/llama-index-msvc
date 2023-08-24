#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import dataclasses
import os
import sys
import logging
import gin

from aiohttp import web
from pybars import Compiler
from llama_index import set_global_service_context
from llama_index import StorageContext, ServiceContext, load_index_from_storage
from processors.embedding import get_embedding
from processors.retriever import HybridRetriever
from processors.llm import get_generator

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

routes = web.RouteTableDef()


@routes.get("/")
async def hello(_: web.Request):
    return web.Response(text="Hello, world")


@gin.configurable
def get_retriever(app, mode):
    if mode != "hybrid" and mode != "embedding" and mode != "keyword":
        return None
    return app[mode]


# curl -v -d 'input=中国有多大' http://127.0.0.1:8080/query
@routes.post("/query")
async def query(request: web.Request):
    req = await request.json()
    turns = req.get("turns", [])
    prompt = req.get("prompt", "")

    if len(prompt) == 0:
        prompt = request.app['prompt']

    if len(turns) == 0:
        return web.json_response({"errMsg": f'input type is not str'})

    if turns[0].get("role", "") != "user":
        return web.json_response({"errMsg": f'first turn is not from user'})
    if turns[-1].get("role", "") != "user":
        return web.json_response({"errMsg": f'last turn is not from user'})

    user_input = turns[-1].get("content", "")

    retriever = get_retriever(request.app)

    # What is the result here?
    context = retriever.retrieve(user_input)

    template = request.app['compiler'].compile(prompt)

    new_prompt = template({"query": user_input, "context": context})

    llm = request.app['llm']

    # So that we can use different llm.
    resp = await llm.agenerate(new_prompt, turns)

    return web.json_response(dataclasses.asdict(resp))


@routes.post("/retrieve")
async def retrieve(request: web.Request):
    req = await request.json()
    turns = req.get("turns", [])
    prompt = req.get("prompt", "")
    if len(prompt) == 0:
        prompt = request.app['prompt']
    if len(turns) == 0:
        return web.json_response({"errMsg": f'input type is not str'})
    if turns[-1].get("role", "") != "user":
        return web.json_response({"errMsg": f'last turn is not from user'})

    user_input = turns[-1].get("content", "")

    retriever = get_retriever(request.app)

    # What is the result here?
    context = retriever.retrieve(user_input)

    resp = {"reply": context}
    return web.json_response(resp)


def init_app(embedding_index, keyword_index):
    app = web.Application()
    app.add_routes(routes)
    embedding_retriever = embedding_index.as_retriever()
    keyword_retriever = keyword_index.as_retriever()
    app['hybrid'] = HybridRetriever(
        embedding_retriever,
        keyword_retriever
    )

    app['keyword'] = keyword_retriever
    app['embedding'] = embedding_retriever

    app["llm"] = get_generator()

    app['compiler'] = Compiler()
    app['prompt'] = "We have provided context information below. \n" \
        "---------------------\n"\
        "{{context}}"\
        "\n---------------------\n"\
        "Given this information, please answer the question: {{query}}\n"
    return app


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Where is the index saved?")
        sys.exit(1)

    p = sys.argv[1]

    gin.parse_config_file('serve.gin')

    if not os.path.isdir(p):
        sys.exit(1)

    service_context = ServiceContext.from_defaults(
        llm=None,
        llm_predictor=None,
        embed_model=get_embedding())

    set_global_service_context(service_context)

    storage_context = StorageContext.from_defaults(persist_dir=p)
    embedding_index = load_index_from_storage(storage_context, index_id="embedding")
    keyword_index = load_index_from_storage(storage_context, index_id="keyword")
    web.run_app(init_app(embedding_index, keyword_index))
