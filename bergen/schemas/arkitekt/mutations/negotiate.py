from bergen.query import TypedGQL
from bergen.schema import Transcript


NEGOTIATION_GQL = TypedGQL("""

  mutation Negotiate(
      $clientType: ClientTypeInput!
      $inward: String,
      $outward: String,
      $port: Int,
      $internal: Boolean,
      $version: String,
      $pointType: DataPointTypeInput,
      $needsNegotiation: Boolean
      
      ) {
  negotiate(
      clientType: $clientType,
      inward: $inward,
      outward: $outward,
      port: $port,
      internal: $internal,
      version: $version,
      pointType: $pointType,
      needsNegotiation: $needsNegotiation
  ) {
    timestamp
    wards {
        distinct
        type
        needsNegotiation
        host
        port
    }
    models {
        identifier
        point {
            distinct
        }
    }
    postman {
        type
        kwargs
    }
    provider {
        type
        kwargs
    }
    host {
        type
        kwargs
    }
  }
  }
""", Transcript)