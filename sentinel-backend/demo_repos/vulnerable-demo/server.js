const express = require('express');
const { exec } = require('child_process');
const fs = require('fs');
const jwt = require('jsonwebtoken');
const { Client } = require('pg');
const axios = require('axios');

const app = express();
app.use(express.json());

// 1. Hardcoded Secret (CWE-798)
const JWT_SECRET = "super_secret_key_12345_do_not_share_in_prod";
const AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE";
const AWS_SECRET_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY";

// 2. OS Command Injection (CWE-78)
app.get('/ping', (req, res) => {
    const ip = req.query.ip;
    // VULNERABILITY: Unsanitized user input passed directly to shell
    exec(`ping -c 4 ${ip}`, (error, stdout, stderr) => {
        if (error) return res.send(stderr);
        res.send(stdout);
    });
});

// 3. Path Traversal / Arbitrary File Read (CWE-22)
app.get('/download', (req, res) => {
    const filename = req.query.file;
    // VULNERABILITY: Reading files without sanitizing paths allows reading /etc/passwd
    const data = fs.readFileSync(`./public/downloads/${filename}`, 'utf8');
    res.send(data);
});

// 4. Server-Side Request Forgery (SSRF) (CWE-918)
app.get('/fetch', async (req, res) => {
    const url = req.query.url;
    // VULNERABILITY: Fetching arbitrary internal or external URLs
    try {
        const response = await axios.get(url);
        res.send(response.data);
    } catch (err) {
        res.status(500).send("Error");
    }
});

// 5. Cross-Site Scripting (Reflected XSS) (CWE-79)
app.get('/greet', (req, res) => {
    const name = req.query.name;
    // VULNERABILITY: Reflected XSS by returning unescaped user input in HTML
    res.send(`<html><body><h1>Hello ${name}!</h1></body></html>`);
});

// 6. SQL Injection (CWE-89)
app.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const client = new Client();
    await client.connect();
    // VULNERABILITY: String concatenation in SQL query
    const result = await client.query(`SELECT * FROM users WHERE username = '${username}' AND password = '${password}'`);
    res.send(result.rows);
});

// 7. Code Injection / Eval (CWE-94)
app.post('/math', (req, res) => {
    const expression = req.body.expression;
    // VULNERABILITY: Executing arbitrary JS via eval()
    const result = eval(expression);
    res.send({ result });
});

app.listen(3000, () => console.log('Server running on port 3000'));
