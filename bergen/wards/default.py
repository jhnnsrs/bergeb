from bergen.console import console

GraphQLWard = None
MainWard = None

try:
    from bergen.wards.gql.aiohttp import AIOHttpGraphQLWard
    GraphQLWard = AIOHttpGraphQLWard
except ImportError as e:
    console.log("No installed GQL Transport. Using bare aiohttp")
    from bergen.wards.bare.aiohttp import AIOHttpWard
    GraphQLWard = AIOHttpWard


try:
    from bergen.wards.gql.main import MainWard as GQLMainWard
    MainWard = GQLMainWard

except ImportError as e:
    console.log("No installed GQL Transport. Using bare aiohttp")
    from bergen.wards.bare.main  import MainWard as BareMainWard
    MainWard = BareMainWard