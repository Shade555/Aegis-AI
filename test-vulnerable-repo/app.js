function deleteUser(userId) {
    // Vulnerability 1: Hardcoded AWS Key
    const awsKey = "AKIAIOSFODNN7EXAMPLE";
    
    // Vulnerability 2: SQL Injection using template literal
    const query = `DELETE FROM users WHERE id = ${userId}`;
    db.execute(query);
}

function processPayment() {
    // XSS vulnerability pattern might be needed, let's just do more secrets
    const githubToken = "ghp_1234567890abcdef1234567890abcdef1234";
}
