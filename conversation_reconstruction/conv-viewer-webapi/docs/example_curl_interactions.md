# Example CURL commands for interaction

The following examples assume your are running the service locally,
and have the following variable set:

```
export SERVER_ADDR="http://localhost:8080"
```

### Get conversation actions within a revision.

```
curl -H "Content-Type: application/json" -X GET \
  ${SERVER_ADDR}/api/cnversation/159766698.0.0
```
