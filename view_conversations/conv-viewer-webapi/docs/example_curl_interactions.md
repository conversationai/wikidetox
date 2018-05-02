# Example CURL commands for interaction

The following examples assume your are running the service locally,
and have the following variable set:

```
export SERVER_ADDR="http://localhost:8080"
```

### Get conversation actions search.

```
curl -H "Content-Type: application/json" -X GET \
  "${SERVER_ADDR}/api/conversation-id/159766698.0.0"
```

```
curl -H "Content-Type: application/json" -X GET \
  "${SERVER_ADDR}/api/revision-id/159766698"
```

```
curl -H "Content-Type: application/json" -X GET \
  "${SERVER_ADDR}/api/page-id/13399738"
```

```
curl -H "Content-Type: application/json" -X GET \
  "${SERVER_ADDR}/api/page-title/User%20talk:213.40.118.71"
```

```
curl -H "Content-Type: application/json" -X GET \
  "${SERVER_ADDR}/api/search/conversation_id/=/159766698.0.0"
```
