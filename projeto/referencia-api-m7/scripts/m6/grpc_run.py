import json, sys, time
from concurrent import futures
sys.path.insert(0, "grpc_demo")
import grpc
import catalog_pb2 as pb
import catalog_pb2_grpc as rpc
from apps.catalog.models import Product


def para_msg(p):
    return pb.Product(id=p.pk, sku=p.sku, name=p.name, price=str(p.price), stock=p.stock)


class Catalog(rpc.CatalogServicer):
    def GetProduct(self, request, context):
        p = Product.objects.filter(pk=request.id, is_active=True).first()
        if p is None:
            context.abort(grpc.StatusCode.NOT_FOUND, "produto não encontrado")
        return para_msg(p)

    def ListProducts(self, request, context):
        for p in Product.objects.filter(is_active=True).order_by("name")[: request.limit or 5]:
            yield para_msg(p)


servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=2))
rpc.add_CatalogServicer_to_server(Catalog(), servidor)
porta = servidor.add_insecure_port("127.0.0.1:0")
servidor.start()

with grpc.insecure_channel(f"127.0.0.1:{porta}") as canal:
    cli = rpc.CatalogStub(canal)
    p = cli.GetProduct(pb.GetProductRequest(id=2))
    print("GetProduct(2) →", p.sku, p.name, p.price)
    try:
        cli.GetProduct(pb.GetProductRequest(id=9999))
    except grpc.RpcError as e:
        print("GetProduct(9999) →", e.code().name, "|", e.details())
    itens = list(cli.ListProducts(pb.ListProductsRequest(limit=3)))
    print("ListProducts(3) (stream) →", [i.sku for i in itens])

    binario = p.SerializeToString()
    como_json = json.dumps({"id": p.id, "sku": p.sku, "name": p.name, "price": p.price, "stock": p.stock}, separators=(",", ":")).encode()
    print(f"\nmesmo produto: protobuf = {len(binario)} bytes | JSON = {len(como_json)} bytes")
    print("bytes do protobuf:", binario.hex(" "))
servidor.stop(0)
