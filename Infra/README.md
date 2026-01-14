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

# Notes

- Do not store sensitive data in the template bucket (it is public).
- Only CloudFormation templates should live in this bucket.
- All runtime resources are created by RootStack.

---

