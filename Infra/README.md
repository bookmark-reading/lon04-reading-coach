# Deployment manual – Bookmark Reading MVP (Infrastructure)

This document explains how to deploy the solution from this repository using the AWS Console.

Current repository structure:

```
Infra
├── README.md
├── SolutionCFN
│   ├── ApiStack.yml
│   ├── AuthStack.yml
│   ├── DataStack.yml
│   ├── README.md
│   └── RootStack.yml
└── TemplateS3.yml
```

---

# Deployment flow (high level)

1. Deploy `TemplateS3.yml` (located in `Infra/`) to create a public S3 bucket for CloudFormation templates.
2. Upload all CloudFormation templates from `Infra/SolutionCFN/` to this bucket.
3. Copy the public HTTPS URL of `RootStack.yml`.
4. Use this URL to deploy the full solution from CloudFormation.

---

# Step 1 – Deploy TemplateS3.yml

File used:

```
Infra/TemplateS3.yml
```

`TemplateS3.yml` creates an S3 bucket used to store CloudFormation templates.

Important:
- The bucket is **publicly readable**.
- CloudFormation must be able to download nested templates over HTTPS.
- Only infrastructure templates are stored here (no runtime data).

### Deploy via AWS Console

1. Open **AWS Console**
2. Go to **CloudFormation**
3. Click **Create stack → With new resources (standard)**
4. Choose **Upload a template file**
5. Upload `TemplateS3.yml`
6. Click **Next**

Stack details:
- Stack name: `bookmark-reading-template-bucket`
- Keep default parameter values

7. Click **Next → Next → Create stack**
8. Wait until status = `CREATE_COMPLETE`

Result:
- Public S3 bucket created
- Used only to host CloudFormation templates

---

# Step 2 – Upload templates to S3

Upload templates from:

```
Infra/SolutionCFN/
```

Files to upload:

```
RootStack.yml
ApiStack.yml
AuthStack.yml
DataStack.yml
```

### Upload via AWS Console

1. Go to **S3**
2. Open your template bucket (created in step 1)
3. Click **Upload**
4. Select the four files listed above
5. Click **Upload**

Confirm the files appear in the bucket root.

---

# Step 3 – Get RootStack public URL

1. In S3, click `RootStack.yml`
2. Click **Copy URL**

Example format:

```
https://<bucket-name>.s3.<region>.amazonaws.com/RootStack.yml
```

This URL is required for deployment.

---

# Step 4 – Deploy full solution

1. Go to **CloudFormation**
2. Click **Create stack → With new resources (standard)**
3. Choose **Amazon S3 URL**
4. Paste the RootStack.yml URL
5. Click **Next**

### Parameters

Provide values as required:
- Template bucket suffix
- Books bucket suffix
- Cognito domain prefix
- DynamoDB table names

(Default values are safe for MVP)

6. Click **Next → Next**
7. Acknowledge IAM permissions
8. Click **Create stack**

---

# Deployment result

CloudFormation creates:

- Cognito User Pool + Hosted UI
- API Gateway + Lambda functions
- DynamoDB tables
- Books S3 bucket

Deployment is complete when:

```
Status = CREATE_COMPLETE
```

You can monitor progress in **CloudFormation → Events**.

---

# Deployment result

CloudFormation creates:

- Cognito User Pool + Hosted UI
- API Gateway + Lambda functions
- DynamoDB tables
- Books S3 bucket

Deployment is complete when:

```
Status = CREATE_COMPLETE
```

You can monitor progress in **CloudFormation → Events**.

---

# How to retrieve and export stack outputs

After deployment, important values (API URL, Cognito IDs, bucket names, etc.) are exposed as **CloudFormation outputs**.

### Quick export (manual)

1. Open **AWS Console → CloudFormation**
2. Click your **RootStack**
3. Open the **Outputs** tab
4. Copy the values you need and export them locally, for example:

```bash
export API=<ApiBaseUrl>
export USER_POOL_ID=<UserPoolId>
export CLIENT_ID=<UserPoolClientId>
```

RootStack exposes outputs from all nested stacks, so you usually only need this one screen.

---

# How to get outputs (for testing and integration)

After deployment, all required integration values are exposed as **outputs of RootStack**.

### How to retrieve outputs in AWS Console

1. Open **AWS Console**
2. Navigate to **CloudFormation**
3. Select your main stack (created from `RootStack.yml`)
4. Open the **Outputs** tab

You will see a list of key/value pairs. These are the values used for testing, API calls and integrations.

You can copy any value and export it locally, for example:

```bash
export API_BASE_URL=<ApiBaseUrl>
export USER_POOL_ID=<UserPoolId>
export CLIENT_ID=<UserPoolClientId>
```

RootStack surfaces outputs from all nested stacks, so you only need this one screen.

---

# Output reference

| Output name | What it is | Used for |
|-------------|------------|----------|
| ApiBaseUrl | API Gateway base URL | Calling backend endpoints (`/health`, `/profile`, `/books`) |
| HostedUiBaseUrl | Cognito Hosted UI base URL | User login and OAuth flows (`/login`, `/oauth2/token`) |
| UserPoolId | Cognito User Pool ID | User management, debugging auth issues |
| UserPoolClientId | Cognito App Client ID | OAuth `client_id` during token exchange |
| UserPoolIssuerUrl | JWT issuer URL | Token validation by API Gateway |
| BooksBucketName | S3 bucket name | Storage location of PDF books |
| UserProfilesTableName | DynamoDB table name | Stores user attributes (first name, last name, grade) |
| BooksTableName | DynamoDB table name | Stores book metadata (title, grade, S3 key) |

---

# Notes

- Do not store sensitive data in the template bucket (it is public).
- Only CloudFormation templates should live in this bucket.
- All runtime resources are created by RootStack.

---


