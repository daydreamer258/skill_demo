// 智能任务管理系统 - Rust 加密服务
// 提供数据加密、解密、哈希计算、JWT令牌验证等安全功能
// 使用 Rust 的高性能和内存安全特性

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::env;
use std::fs;
use std::path::Path;
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};

// ==================== 错误处理 ====================

/// 自定义错误类型
#[derive(Debug)]
pub enum CryptoError {
    /// 加密错误
    EncryptionError(String),
    /// 解密错误
    DecryptionError(String),
    /// 哈希错误
    HashError(String),
    /// 密钥错误
    KeyError(String),
    /// 令牌错误
    TokenError(String),
    /// 配置错误
    ConfigError(String),
    /// IO错误
    IoError(std::io::Error),
}

impl From<std::io::Error> for CryptoError {
    fn from(err: std::io::Error) -> Self {
        CryptoError::IoError(err)
    }
}

impl std::fmt::Display for CryptoError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            CryptoError::EncryptionError(msg) => write!(f, "加密错误: {}", msg),
            CryptoError::DecryptionError(msg) => write!(f, "解密错误: {}", msg),
            CryptoError::HashError(msg) => write!(f, "哈希错误: {}", msg),
            CryptoError::KeyError(msg) => write!(f, "密钥错误: {}", msg),
            CryptoError::TokenError(msg) => write!(f, "令牌错误: {}", msg),
            CryptoError::ConfigError(msg) => write!(f, "配置错误: {}", msg),
            CryptoError::IoError(err) => write!(f, "IO错误: {}", err),
        }
    }
}

impl std::error::Error for CryptoError {}

/// 结果类型别名
pub type Result<T> = std::result::Result<T, CryptoError>;

// ==================== 配置结构体 ====================

/// 加密服务配置
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CryptoConfig {
    /// 主密钥（用于数据加密）
    pub master_key: String,
    /// JWT签名密钥
    pub jwt_secret: String,
    /// JWT过期时间（秒）
    pub jwt_expiration: u64,
    /// JWT刷新令牌过期时间（秒）
    pub jwt_refresh_expiration: u64,
    /// 哈希算法迭代次数
    pub hash_iterations: u32,
    /// 盐值长度
    pub salt_length: usize,
    /// 密钥长度
    pub key_length: usize,
}

impl Default for CryptoConfig {
    fn default() -> Self {
        Self {
            master_key: env::var("MASTER_KEY").unwrap_or_else(|_| "default-master-key-change-in-production".to_string()),
            jwt_secret: env::var("JWT_SECRET").unwrap_or_else(|_| "default-jwt-secret-change-in-production".to_string()),
            jwt_expiration: 3600, // 1小时
            jwt_refresh_expiration: 604800, // 7天
            hash_iterations: 100000,
            salt_length: 32,
            key_length: 32,
        }
    }
}

impl CryptoConfig {
    /// 从文件加载配置
    pub fn from_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let content = fs::read_to_string(path)?;
        let config: CryptoConfig = serde_json::from_str(&content)
            .map_err(|e| CryptoError::ConfigError(format!("解析配置失败: {}", e)))?;
        Ok(config)
    }

    /// 从环境变量加载配置
    pub fn from_env() -> Self {
        Self {
            master_key: env::var("MASTER_KEY").unwrap_or_default(),
            jwt_secret: env::var("JWT_SECRET").unwrap_or_default(),
            jwt_expiration: env::var("JWT_EXPIRATION")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(3600),
            jwt_refresh_expiration: env::var("JWT_REFRESH_EXPIRATION")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(604800),
            hash_iterations: env::var("HASH_ITERATIONS")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(100000),
            salt_length: 32,
            key_length: 32,
        }
    }
}

// ==================== 加密服务 ====================

/// 加密服务主结构体
pub struct CryptoService {
    config: Arc<CryptoConfig>,
}

impl CryptoService {
    /// 创建新的加密服务实例
    pub fn new(config: CryptoConfig) -> Self {
        Self {
            config: Arc::new(config),
        }
    }

    /// 使用默认配置创建实例
    pub fn with_defaults() -> Self {
        Self::new(CryptoConfig::default())
    }

    // ==================== 密码哈希功能 ====================

    /// 对密码进行哈希处理
    ///
    /// # 参数
    /// - `password`: 原始密码
    ///
    /// # 返回
    /// - 格式为 "salt:hash" 的哈希字符串
    pub fn hash_password(&self, password: &str) -> Result<String> {
        // 生成随机盐值
        let salt = self.generate_salt()?;

        // 计算哈希值
        let hash = self.compute_hash(password, &salt)?;

        Ok(format!("{}:{}", salt, hash))
    }

    /// 验证密码是否匹配
    ///
    /// # 参数
    /// - `password`: 待验证的密码
    /// - `stored_hash`: 存储的哈希值（格式："salt:hash"）
    ///
    /// # 返回
    /// - 验证是否通过
    pub fn verify_password(&self, password: &str, stored_hash: &str) -> Result<bool> {
        let parts: Vec<&str> = stored_hash.split(':').collect();
        if parts.len() != 2 {
            return Err(CryptoError::HashError("无效的哈希格式".to_string()));
        }

        let salt = parts[0];
        let expected_hash = parts[1];

        let computed_hash = self.compute_hash(password, salt)?;

        // 常量时间比较，防止时序攻击
        Ok(self.constant_time_compare(&computed_hash, expected_hash))
    }

    /// 计算密码哈希值
    fn compute_hash(&self, password: &str, salt: &str) -> Result<String> {
        // 简化的哈希实现（生产环境应使用argon2或bcrypt）
        let mut result = format!("{}{}{}", password, salt, self.config.master_key);

        // 多次迭代
        for i in 0..self.config.hash_iterations {
            result = self.sha256(&format!("{}{}", result, i));
        }

        Ok(result)
    }

    /// 生成随机盐值
    fn generate_salt(&self) -> Result<String> {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| CryptoError::HashError(format!("获取时间失败: {}", e)))?
            .as_nanos();

        let random_part = self.sha256(&format!("{}-random-{}", timestamp, self.config.master_key));

        Ok(random_part[..self.config.salt_length].to_string())
    }

    /// SHA256哈希（简化实现）
    fn sha256(&self, input: &str) -> String {
        // 简化的SHA256实现（实际应使用rust-crypto或ring库）
        let mut hash: u64 = 0xcbf29ce484222325; // FNV偏移基础值

        for byte in input.bytes() {
            hash ^= byte as u64;
            hash = hash.wrapping_mul(0x100000001b3); // FNV质数
        }

        format!("{:016x}", hash)
    }

    /// 常量时间比较
    fn constant_time_compare(&self, a: &str, b: &str) -> bool {
        if a.len() != b.len() {
            return false;
        }

        let mut result = 0u8;
        for (a_byte, b_byte) in a.bytes().zip(b.bytes()) {
            result |= a_byte ^ b_byte;
        }

        result == 0
    }

    // ==================== 数据加密功能 ====================

    /// 加密数据
    ///
    /// # 参数
    /// - `plaintext`: 明文数据
    ///
    /// # 返回
    /// - Base64编码的密文
    pub fn encrypt(&self, plaintext: &str) -> Result<String> {
        // 简化的加密实现（生产环境应使用AES-GCM）
        let key = self.derive_key(&self.config.master_key)?;

        let mut ciphertext = Vec::new();

        for (i, byte) in plaintext.bytes().enumerate() {
            let key_byte = key[i % key.len()];
            ciphertext.push(byte ^ key_byte);
        }

        // 添加校验和
        let checksum = self.calculate_checksum(&ciphertext);
        ciphertext.extend_from_slice(&checksum);

        // Base64编码
        Ok(self.base64_encode(&ciphertext))
    }

    /// 解密数据
    ///
    /// # 参数
    /// - `ciphertext`: Base64编码的密文
    ///
    /// # 返回
    /// - 解密后的明文
    pub fn decrypt(&self, ciphertext: &str) -> Result<String> {
        // Base64解码
        let mut data = self.base64_decode(ciphertext)?;

        // 验证校验和
        if data.len() < 4 {
            return Err(CryptoError::DecryptionError("数据长度不足".to_string()));
        }

        let data_len = data.len() - 4;
        let stored_checksum = &data[data_len..];
        let computed_checksum = self.calculate_checksum(&data[..data_len]);

        if stored_checksum != computed_checksum {
            return Err(CryptoError::DecryptionError("校验和不匹配".to_string()));
        }

        let encrypted_data = &data[..data_len];

        // 解密
        let key = self.derive_key(&self.config.master_key)?;
        let mut plaintext = Vec::new();

        for (i, byte) in encrypted_data.iter().enumerate() {
            let key_byte = key[i % key.len()];
            plaintext.push(byte ^ key_byte);
        }

        String::from_utf8(plaintext)
            .map_err(|e| CryptoError::DecryptionError(format!("UTF-8解码失败: {}", e)))
    }

    /// 派生密钥
    fn derive_key(&self, master_key: &str) -> Result<Vec<u8>> {
        let mut key = Vec::with_capacity(self.config.key_length);

        let hash = self.sha256(master_key);
        for (i, c) in hash.chars().enumerate() {
            if i >= self.config.key_length {
                break;
            }
            key.push(c as u8);
        }

        Ok(key)
    }

    /// 计算校验和
    fn calculate_checksum(&self, data: &[u8]) -> [u8; 4] {
        let mut sum: u32 = 0;
        for (i, byte) in data.iter().enumerate() {
            sum = sum.wrapping_add((*byte as u32).wrapping_mul((i + 1) as u32));
        }
        sum.to_be_bytes()
    }

    /// Base64编码
    fn base64_encode(&self, data: &[u8]) -> String {
        const ALPHABET: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

        let mut result = String::new();
        let mut i = 0;

        while i < data.len() {
            let b0 = data[i] as usize;
            let b1 = if i + 1 < data.len() { data[i + 1] as usize } else { 0 };
            let b2 = if i + 2 < data.len() { data[i + 2] as usize } else { 0 };

            result.push(ALPHABET[b0 >> 2] as char);
            result.push(ALPHABET[((b0 & 0x03) << 4) | (b1 >> 4)] as char);

            if i + 1 < data.len() {
                result.push(ALPHABET[((b1 & 0x0f) << 2) | (b2 >> 6)] as char);
            } else {
                result.push('=');
            }

            if i + 2 < data.len() {
                result.push(ALPHABET[b2 & 0x3f] as char);
            } else {
                result.push('=');
            }

            i += 3;
        }

        result
    }

    /// Base64解码
    fn base64_decode(&self, input: &str) -> Result<Vec<u8>> {
        const DECODE_TABLE: [i8; 128] = [
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
            -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
            52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
            -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
            15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
            -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
            41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1,
        ];

        let input = input.trim_end_matches('=');
        let mut result = Vec::with_capacity(input.len() * 3 / 4);

        let chars: Vec<char> = input.chars().collect();
        let mut i = 0;

        while i < chars.len() {
            let c0 = chars[i] as usize;
            let c1 = if i + 1 < chars.len() { chars[i + 1] as usize } else { 0 };

            let v0 = if c0 < 128 { DECODE_TABLE[c0] } else { -1 };
            let v1 = if c1 < 128 { DECODE_TABLE[c1] } else { -1 };

            if v0 < 0 || v1 < 0 {
                return Err(CryptoError::DecryptionError("无效的Base64字符".to_string()));
            }

            result.push(((v0 as u8) << 2) | ((v1 as u8) >> 4));

            if i + 2 < chars.len() {
                let c2 = chars[i + 2] as usize;
                let v2 = if c2 < 128 { DECODE_TABLE[c2] } else { -1 };

                if v2 >= 0 {
                    result.push(((v1 as u8) << 4) | ((v2 as u8) >> 2));

                    if i + 3 < chars.len() {
                        let c3 = chars[i + 3] as usize;
                        let v3 = if c3 < 128 { DECODE_TABLE[c3] } else { -1 };

                        if v3 >= 0 {
                            result.push(((v2 as u8) << 6) | (v3 as u8));
                        }
                    }
                }
            }

            i += 4;
        }

        Ok(result)
    }

    // ==================== JWT令牌功能 ====================

    /// 生成JWT访问令牌
    ///
    /// # 参数
    /// - `user_id`: 用户ID
    /// - `role`: 用户角色
    ///
    /// # 返回
    /// - JWT令牌字符串
    pub fn generate_access_token(&self, user_id: &str, role: &str) -> Result<String> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| CryptoError::TokenError(format!("获取时间失败: {}", e)))?
            .as_secs();

        let payload = JwtPayload {
            sub: user_id.to_string(),
            role: role.to_string(),
            token_type: "access".to_string(),
            iat: now,
            exp: now + self.config.jwt_expiration,
        };

        self.encode_jwt(&payload)
    }

    /// 生成JWT刷新令牌
    ///
    /// # 参数
    /// - `user_id`: 用户ID
    ///
    /// # 返回
    /// - 刷新令牌字符串
    pub fn generate_refresh_token(&self, user_id: &str) -> Result<String> {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| CryptoError::TokenError(format!("获取时间失败: {}", e)))?
            .as_secs();

        let payload = JwtPayload {
            sub: user_id.to_string(),
            role: String::new(),
            token_type: "refresh".to_string(),
            iat: now,
            exp: now + self.config.jwt_refresh_expiration,
        };

        self.encode_jwt(&payload)
    }

    /// 验证JWT令牌
    ///
    /// # 参数
    /// - `token`: JWT令牌字符串
    ///
    /// # 返回
    /// - 解码后的载荷
    pub fn verify_token(&self, token: &str) -> Result<JwtPayload> {
        let parts: Vec<&str> = token.split('.').collect();
        if parts.len() != 3 {
            return Err(CryptoError::TokenError("无效的令牌格式".to_string()));
        }

        // 验证签名
        let expected_signature = self.sign_jwt(&format!("{}.{}", parts[0], parts[1]));
        if !self.constant_time_compare(&expected_signature, parts[2]) {
            return Err(CryptoError::TokenError("签名验证失败".to_string()));
        }

        // 解码载荷
        let payload_json = self.base64_decode(parts[1])?;
        let payload: JwtPayload = String::from_utf8(payload_json)
            .map_err(|e| CryptoError::TokenError(format!("UTF-8解码失败: {}", e)))
            .and_then(|s| {
                serde_json::from_str(&s)
                    .map_err(|e| CryptoError::TokenError(format!("JSON解析失败: {}", e)))
            })?;

        // 验证过期时间
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_err(|e| CryptoError::TokenError(format!("获取时间失败: {}", e)))?
            .as_secs();

        if payload.exp < now {
            return Err(CryptoError::TokenError("令牌已过期".to_string()));
        }

        Ok(payload)
    }

    /// 编码JWT
    fn encode_jwt(&self, payload: &JwtPayload) -> Result<String> {
        let header = JwtHeader {
            alg: "HS256".to_string(),
            typ: "JWT".to_string(),
        };

        let header_json = serde_json::to_string(&header)
            .map_err(|e| CryptoError::TokenError(format!("序列化头部失败: {}", e)))?;
        let payload_json = serde_json::to_string(payload)
            .map_err(|e| CryptoError::TokenError(format!("序列化载荷失败: {}", e)))?;

        let header_b64 = self.base64_encode(header_json.as_bytes());
        let payload_b64 = self.base64_encode(payload_json.as_bytes());

        let signature = self.sign_jwt(&format!("{}.{}", header_b64, payload_b64));

        Ok(format!("{}.{}.{}", header_b64, payload_b64, signature))
    }

    /// 签名JWT
    fn sign_jwt(&self, data: &str) -> String {
        self.sha256(&format!("{}{}", data, self.config.jwt_secret))
    }

    // ==================== 数据签名功能 ====================

    /// 对数据进行签名
    ///
    /// # 参数
    /// - `data`: 待签名数据
    ///
    /// # 返回
    /// - 签名字符串
    pub fn sign_data(&self, data: &str) -> String {
        self.sha256(&format!("{}{}{}", data, self.config.master_key, self.config.jwt_secret))
    }

    /// 验证数据签名
    ///
    /// # 参数
    /// - `data`: 原始数据
    /// - `signature`: 签名
    ///
    /// # 返回
    /// - 验证是否通过
    pub fn verify_signature(&self, data: &str, signature: &str) -> bool {
        let expected = self.sign_data(data);
        self.constant_time_compare(&expected, signature)
    }

    // ==================== 安全工具函数 ====================

    /// 生成随机字符串
    ///
    /// # 参数
    /// - `length`: 字符串长度
    ///
    /// # 返回
    /// - 随机字符串
    pub fn generate_random_string(&self, length: usize) -> String {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_nanos();

        let mut result = String::new();

        for i in 0..length {
            let hash = self.sha256(&format!("{}-{}-{}", timestamp, i, self.config.master_key));
            let idx = (i + (timestamp as usize)) % hash.len();
            result.push(hash.chars().nth(idx).unwrap_or('a'));
        }

        result
    }

    /// 生成API密钥
    ///
    /// # 返回
    /// - API密钥字符串
    pub fn generate_api_key(&self) -> String {
        let random = self.generate_random_string(32);
        let prefix = "sk";
        format!("{}_{}", prefix, random)
    }

    /// 计算数据指纹
    ///
    /// # 参数
    /// - `data`: 输入数据
    ///
    /// # 返回
    /// - 指纹字符串
    pub fn calculate_fingerprint(&self, data: &str) -> String {
        let hash = self.sha256(data);
        format!("fp_{}", &hash[..16])
    }

    /// 安全比较两个字符串（防止时序攻击）
    ///
    /// # 参数
    /// - `a`: 第一个字符串
    /// - `b`: 第二个字符串
    ///
    /// # 返回
    /// - 是否相等
    pub fn secure_compare(&self, a: &str, b: &str) -> bool {
        self.constant_time_compare(a, b)
    }
}

// ==================== JWT结构体 ====================

/// JWT头部
#[derive(Debug, Serialize, Deserialize)]
struct JwtHeader {
    alg: String,
    typ: String,
}

/// JWT载荷
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JwtPayload {
    /// 主题（用户ID）
    pub sub: String,
    /// 角色
    pub role: String,
    /// 令牌类型
    pub token_type: String,
    /// 签发时间
    pub iat: u64,
    /// 过期时间
    pub exp: u64,
}

impl JwtPayload {
    /// 检查令牌是否过期
    pub fn is_expired(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        self.exp < now
    }

    /// 获取剩余有效期（秒）
    pub fn remaining_time(&self) -> u64 {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        if self.exp > now {
            self.exp - now
        } else {
            0
        }
    }
}

// ==================== 安全中间件 ====================

/// 安全中间件配置
#[derive(Debug, Clone)]
pub struct SecurityMiddleware {
    crypto: Arc<CryptoService>,
    excluded_paths: Vec<String>,
}

impl SecurityMiddleware {
    /// 创建新的安全中间件
    pub fn new(crypto: CryptoService) -> Self {
        Self {
            crypto: Arc::new(crypto),
            excluded_paths: vec![
                "/health".to_string(),
                "/api/auth/login".to_string(),
                "/api/auth/register".to_string(),
                "/".to_string(),
            ],
        }
    }

    /// 添加排除路径
    pub fn exclude_path(mut self, path: &str) -> Self {
        self.excluded_paths.push(path.to_string());
        self
    }

    /// 检查路径是否需要认证
    pub fn requires_auth(&self, path: &str) -> bool {
        !self.excluded_paths.contains(&path.to_string())
    }

    /// 验证请求令牌
    pub fn authenticate(&self, token: &str) -> Result<JwtPayload> {
        self.crypto.verify_token(token)
    }

    /// 检查权限
    pub fn check_permission(&self, payload: &JwtPayload, required_role: &str) -> bool {
        let role_hierarchy = HashMap::from([
            ("admin", 4),
            ("manager", 3),
            ("user", 2),
            ("guest", 1),
        ]);

        let user_level = role_hierarchy.get(payload.role.as_str()).unwrap_or(&0);
        let required_level = role_hierarchy.get(required_role).unwrap_or(&0);

        user_level >= required_level
    }
}

// ==================== 审计日志 ====================

/// 审计日志记录
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditLog {
    /// 日志ID
    pub id: String,
    /// 用户ID
    pub user_id: String,
    /// 操作类型
    pub action: String,
    /// 资源类型
    pub resource_type: String,
    /// 资源ID
    pub resource_id: String,
    /// 操作详情
    pub details: HashMap<String, String>,
    /// IP地址
    pub ip_address: String,
    /// 时间戳
    pub timestamp: u64,
    /// 状态
    pub status: String,
}

/// 审计日志服务
pub struct AuditService {
    crypto: Arc<CryptoService>,
}

impl AuditService {
    /// 创建新的审计服务
    pub fn new(crypto: CryptoService) -> Self {
        Self {
            crypto: Arc::new(crypto),
        }
    }

    /// 记录审计日志
    pub fn log(&self, log_entry: &AuditLog) -> Result<String> {
        let log_json = serde_json::to_string(log_entry)
            .map_err(|e| CryptoError::ConfigError(format!("序列化日志失败: {}", e)))?;

        // 对日志进行签名以确保完整性
        let signature = self.crypto.sign_data(&log_json);

        println!("[AUDIT] {} - Signature: {}", log_json, signature);

        Ok(signature)
    }

    /// 验证审计日志
    pub fn verify_log(&self, log_json: &str, signature: &str) -> bool {
        self.crypto.verify_signature(log_json, signature)
    }
}

// ==================== 单元测试 ====================

#[cfg(test)]
mod tests {
    use super::*;

    /// 测试密码哈希
    #[test]
    fn test_password_hashing() {
        let crypto = CryptoService::with_defaults();
        let password = "test_password_123";

        let hash = crypto.hash_password(password).unwrap();
        assert!(hash.contains(':'));

        // 验证正确密码
        assert!(crypto.verify_password(password, &hash).unwrap());

        // 验证错误密码
        assert!(!crypto.verify_password("wrong_password", &hash).unwrap());
    }

    /// 测试数据加密解密
    #[test]
    fn test_encryption_decryption() {
        let crypto = CryptoService::with_defaults();
        let plaintext = "敏感数据需要加密保护";

        let ciphertext = crypto.encrypt(plaintext).unwrap();
        assert_ne!(ciphertext, plaintext);

        let decrypted = crypto.decrypt(&ciphertext).unwrap();
        assert_eq!(decrypted, plaintext);
    }

    /// 测试JWT令牌生成和验证
    #[test]
    fn test_jwt_tokens() {
        let crypto = CryptoService::with_defaults();

        let access_token = crypto.generate_access_token("user123", "admin").unwrap();
        assert!(!access_token.is_empty());

        let payload = crypto.verify_token(&access_token).unwrap();
        assert_eq!(payload.sub, "user123");
        assert_eq!(payload.role, "admin");
        assert_eq!(payload.token_type, "access");
    }

    /// 测试刷新令牌
    #[test]
    fn test_refresh_token() {
        let crypto = CryptoService::with_defaults();

        let refresh_token = crypto.generate_refresh_token("user456").unwrap();
        let payload = crypto.verify_token(&refresh_token).unwrap();

        assert_eq!(payload.sub, "user456");
        assert_eq!(payload.token_type, "refresh");
    }

    /// 测试数据签名
    #[test]
    fn test_data_signing() {
        let crypto = CryptoService::with_defaults();
        let data = "重要数据";

        let signature = crypto.sign_data(data);
        assert!(!signature.is_empty());

        assert!(crypto.verify_signature(data, &signature));
        assert!(!crypto.verify_signature("篡改数据", &signature));
    }

    /// 测试随机字符串生成
    #[test]
    fn test_random_string_generation() {
        let crypto = CryptoService::with_defaults();

        let str1 = crypto.generate_random_string(32);
        let str2 = crypto.generate_random_string(32);

        assert_eq!(str1.len(), 32);
        assert_eq!(str2.len(), 32);
        // 注意：由于我们使用时间戳，连续调用可能产生相同结果
        // 在实际应用中应使用真正的随机数生成器
    }

    /// 测试API密钥生成
    #[test]
    fn test_api_key_generation() {
        let crypto = CryptoService::with_defaults();

        let api_key = crypto.generate_api_key();
        assert!(api_key.starts_with("sk_"));
        assert!(api_key.len() > 32);
    }

    /// 测试安全中间件
    #[test]
    fn test_security_middleware() {
        let crypto = CryptoService::with_defaults();
        let middleware = SecurityMiddleware::new(crypto);

        // 测试排除路径
        assert!(!middleware.requires_auth("/health"));
        assert!(!middleware.requires_auth("/api/auth/login"));

        // 测试需要认证的路径
        assert!(middleware.requires_auth("/api/tasks"));
        assert!(middleware.requires_auth("/api/users/me"));
    }

    /// 测试权限检查
    #[test]
    fn test_permission_check() {
        let crypto = CryptoService::with_defaults();
        let middleware = SecurityMiddleware::new(crypto);

        let admin_payload = JwtPayload {
            sub: "admin1".to_string(),
            role: "admin".to_string(),
            token_type: "access".to_string(),
            iat: 0,
            exp: u64::MAX,
        };

        assert!(middleware.check_permission(&admin_payload, "admin"));
        assert!(middleware.check_permission(&admin_payload, "manager"));
        assert!(middleware.check_permission(&admin_payload, "user"));

        let user_payload = JwtPayload {
            sub: "user1".to_string(),
            role: "user".to_string(),
            token_type: "access".to_string(),
            iat: 0,
            exp: u64::MAX,
        };

        assert!(!middleware.check_permission(&user_payload, "admin"));
        assert!(!middleware.check_permission(&user_payload, "manager"));
        assert!(middleware.check_permission(&user_payload, "user"));
    }

    /// 测试审计日志
    #[test]
    fn test_audit_log() {
        let crypto = CryptoService::with_defaults();
        let audit = AuditService::new(crypto);

        let log_entry = AuditLog {
            id: "log001".to_string(),
            user_id: "user123".to_string(),
            action: "LOGIN".to_string(),
            resource_type: "session".to_string(),
            resource_id: "session001".to_string(),
            details: HashMap::from([
                ("browser".to_string(), "Chrome".to_string()),
                ("os".to_string(), "Windows".to_string()),
            ]),
            ip_address: "192.168.1.1".to_string(),
            timestamp: 1234567890,
            status: "success".to_string(),
        };

        let signature = audit.log(&log_entry).unwrap();
        assert!(!signature.is_empty());
    }
}

// ==================== 主函数 ====================

fn main() {
    println!("智能任务管理系统 - Rust 加密服务");
    println!("=====================================");

    // 创建加密服务
    let crypto = CryptoService::with_defaults();

    // 示例：密码哈希
    println!("\n1. 密码哈希测试:");
    let password = "MySecurePassword123!";
    let hash = crypto.hash_password(password).unwrap();
    println!("   原始密码: {}", password);
    println!("   哈希值: {}", hash);
    println!("   验证结果: {}", crypto.verify_password(password, &hash).unwrap());

    // 示例：数据加密
    println!("\n2. 数据加密测试:");
    let plaintext = "这是需要加密的敏感数据";
    let ciphertext = crypto.encrypt(plaintext).unwrap();
    let decrypted = crypto.decrypt(&ciphertext).unwrap();
    println!("   明文: {}", plaintext);
    println!("   密文: {}", ciphertext);
    println!("   解密: {}", decrypted);

    // 示例：JWT令牌
    println!("\n3. JWT令牌测试:");
    let token = crypto.generate_access_token("user001", "admin").unwrap();
    let payload = crypto.verify_token(&token).unwrap();
    println!("   访问令牌: {}...", &token[..50]);
    println!("   用户ID: {}", payload.sub);
    println!("   角色: {}", payload.role);
    println!("   剩余有效期: {}秒", payload.remaining_time());

    // 示例：API密钥生成
    println!("\n4. API密钥生成:");
    let api_key = crypto.generate_api_key();
    println!("   API密钥: {}", api_key);

    // 示例：数据签名
    println!("\n5. 数据签名测试:");
    let data = "重要业务数据";
    let signature = crypto.sign_data(data);
    println!("   原始数据: {}", data);
    println!("   签名: {}", signature);
    println!("   验证结果: {}", crypto.verify_signature(data, &signature));

    println!("\n=====================================");
    println!("加密服务演示完成!");
}