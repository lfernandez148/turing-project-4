# Protected Images

This folder contains sensitive images that require authentication to access.

## How to access protected images:

### 1. Include authentication token in header:
```
Authorization: Bearer your-secret-token
```

### 2. Valid tokens (for demo):
- `your-secret-token`
- `campaign-admin-2024`
- `protected-access-key`

### 3. Access via protected endpoint:
```
GET /protected/images/sensitive-report.jpg
Authorization: Bearer your-secret-token
```

### 4. Direct access will be blocked:
```
GET /images/protected/sensitive-report.jpg  ❌ FORBIDDEN
```
