"""
深度学习检测模块 - DL-based Attack Detection
使用PyTorch构建的神经网络模型用于检测未知攻击
"""
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, List, Dict, Any
import numpy as np
from pathlib import Path
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class DLDetectionModel(nn.Module):
    """深度学习攻击检测模型 - 多层神经网络"""
    
    def __init__(self, input_size: int = 256, hidden_size: int = 128, 
                 num_classes: int = 2, dropout: float = 0.3):
        """
        初始化模型
        
        Args:
            input_size: 输入特征维度（字符串编码后）
            hidden_size: 隐藏层维度
            num_classes: 输出类别数（2: 正常/攻击）
            dropout: Dropout率
        """
        super(DLDetectionModel, self).__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_classes = num_classes
        
        # 构建网络
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.bn1 = nn.BatchNorm1d(hidden_size)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(dropout)
        
        self.fc2 = nn.Linear(hidden_size, hidden_size // 2)
        self.bn2 = nn.BatchNorm1d(hidden_size // 2)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(dropout)
        
        self.fc3 = nn.Linear(hidden_size // 2, hidden_size // 4)
        self.bn3 = nn.BatchNorm1d(hidden_size // 4)
        self.relu3 = nn.ReLU()
        self.dropout3 = nn.Dropout(dropout)
        
        self.fc4 = nn.Linear(hidden_size // 4, num_classes)
        self.softmax = nn.Softmax(dim=1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """前向传播"""
        x = self.dropout1(self.relu1(self.bn1(self.fc1(x))))
        x = self.dropout2(self.relu2(self.bn2(self.fc2(x))))
        x = self.dropout3(self.relu3(self.bn3(self.fc3(x))))
        x = self.fc4(x)
        return x


class FeatureExtractor:
    """从HTTP请求中提取特征"""
    
    def __init__(self, feature_dim: int = 256):
        """初始化特征提取器"""
        self.feature_dim = feature_dim
        self.char_set = set()
        self._build_char_set()
    
    def _build_char_set(self):
        """构建字符集"""
        # 包括常见的Web攻击特征字符
        self.char_set = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                           '!@#$%^&*()_+-=[]{}|;:\'",.<>?/\\`~ ')
        self.char_to_idx = {char: idx for idx, char in enumerate(sorted(self.char_set))}
    
    def extract_features(self, request_text: str) -> np.ndarray:
        """
        从请求文本提取特征向量
        
        Args:
            request_text: HTTP请求的文本表示
            
        Returns:
            特征向量 (feature_dim,)
        """
        features = np.zeros(self.feature_dim)
        # 仅保留允许字符并限制长度，防止异常字符和超长输入
        text = request_text.lower()[:1000]
        text = ''.join(ch for ch in text if ch in self.char_set)
        
        # 特征1-5: 基本统计
        features[0] = len(text)  # 请求长度
        features[1] = text.count('select') + text.count('insert') + text.count('delete')  # SQL关键字
        features[2] = text.count('<') + text.count('>')  # HTML标签
        features[3] = text.count('%') + text.count('\\x')  # 编码字符
        features[4] = text.count('../') + text.count('..\\')  # 目录遍历
        
        # 特征5-10: 特殊字符统计
        features[5] = text.count(';')
        features[6] = text.count('(') + text.count(')')
        features[7] = text.count('\'') + text.count('"')
        features[8] = text.count('=')
        features[9] = text.count('&')
        
        # 特征10+: 字符频率（简化版）
        for i, char in enumerate(sorted(self.char_set)[:self.feature_dim-10]):
            features[10 + i] = text.count(char)
        
        # 归一化
        max_val = np.max(np.abs(features)) + 1e-6
        features = features / max_val
        
        return features


class DLDetector:
    """深度学习检测器 - 管理模型训练和推理"""
    
    def __init__(self, model_path: str = "models/saved/dl_model.pth",
                 feature_dim: int = 256, device: str = None):
        """
        初始化检测器
        
        Args:
            model_path: 模型保存路径
            feature_dim: 特征维度
            device: 使用的设备（cpu或cuda）
        """
        self.model_path = Path(model_path)
        self.feature_dim = feature_dim
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        
        self.feature_extractor = FeatureExtractor(feature_dim)
        self.model = DLDetectionModel(input_size=feature_dim)
        self.model.to(self.device)
        
        self.training_history = []
        self.load_model()
    
    def load_model(self):
        """加载已训练的模型"""
        if self.model_path.exists():
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device)
                self.model.load_state_dict(checkpoint['model_state_dict'])
                self.training_history = checkpoint.get('history', [])
                logger.info(f"模型加载成功: {self.model_path}")
            except Exception as e:
                logger.warning(f"加载模型失败: {e}，使用随机初始化")
                self._initialize_model()
        else:
            self._initialize_model()
    
    def _initialize_model(self):
        """初始化模型权重"""
        for param in self.model.parameters():
            if len(param.shape) > 1:
                nn.init.xavier_uniform_(param)
            else:
                nn.init.zeros_(param)
    
    def predict(self, request_text: str, threshold: float = 0.5) -> Tuple[bool, float, Dict[str, Any]]:
        """
        预测请求是否为攻击
        
        Args:
            request_text: HTTP请求文本
            threshold: 攻击置信度阈值
            
        Returns:
            (是否为攻击, 攻击置信度, 详细信息)
        """
        self.model.eval()
        
        try:
            # 特征提取
            features = self.feature_extractor.extract_features(request_text)
            x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
            
            # 推理
            with torch.no_grad():
                logits = self.model(x)
                probs = torch.softmax(logits, dim=1)
            
            # 获取预测结果
            attack_prob = probs[0, 1].item()  # 类别1：攻击
            is_attack = attack_prob > threshold
            
            details = {
                'confidence': attack_prob,
                'threshold': threshold,
                'normal_prob': probs[0, 0].item(),
                'request_length': len(request_text)
            }
            
            return is_attack, attack_prob, details
        
        except Exception as e:
            logger.error(f"模型预测失败: {e}")
            return False, 0.0, {'error': str(e)}
    
    def train(self, train_loader, val_loader=None, epochs: int = 10, 
              learning_rate: float = 0.001, save_interval: int = 5):
        """
        训练模型
        
        Args:
            train_loader: 训练数据加载器
            val_loader: 验证数据加载器
            epochs: 训练轮数
            learning_rate: 学习率
            save_interval: 保存间隔（轮）
        """
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, 'min', patience=3)
        
        self.model.train()
        
        for epoch in range(epochs):
            train_loss = 0.0
            correct = 0
            total = 0
            
            for features, labels in train_loader:
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                # 前向传播
                outputs = self.model(features)
                loss = criterion(outputs, labels)
                
                # 反向传播
                optimizer.zero_grad()
                loss.backward()
                optimizer.step()
                
                # 统计
                train_loss += loss.item()
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)
            
            train_acc = correct / total if total > 0 else 0
            avg_loss = train_loss / len(train_loader) if train_loader else 0
            
            # 验证
            val_loss = 0.0
            val_acc = 0.0
            if val_loader:
                val_loss, val_acc = self._validate(val_loader, criterion)
                scheduler.step(val_loss)
            
            # 记录
            history = {
                'epoch': epoch + 1,
                'train_loss': avg_loss,
                'train_acc': train_acc,
                'val_loss': val_loss,
                'val_acc': val_acc,
                'timestamp': datetime.now().isoformat()
            }
            self.training_history.append(history)
            
            logger.info(f"Epoch {epoch+1}/{epochs} - Loss: {avg_loss:.4f}, Acc: {train_acc:.4f}")
            
            # 定期保存
            if (epoch + 1) % save_interval == 0:
                self.save_model()
    
    def _validate(self, val_loader, criterion) -> Tuple[float, float]:
        """验证模型"""
        self.model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for features, labels in val_loader:
                features = features.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(features)
                loss = criterion(outputs, labels)
                val_loss += loss.item()
                
                _, predicted = torch.max(outputs, 1)
                correct += (predicted == labels).sum().item()
                total += labels.size(0)
        
        self.model.train()
        return val_loss / len(val_loader) if val_loader else 0, correct / total if total > 0 else 0
    
    def save_model(self):
        """保存模型"""
        self.model_path.parent.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            'model_state_dict': self.model.state_dict(),
            'history': self.training_history,
            'feature_dim': self.feature_dim,
            'timestamp': datetime.now().isoformat()
        }
        
        torch.save(checkpoint, self.model_path)
        logger.info(f"模型已保存: {self.model_path}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        
        return {
            'model_path': str(self.model_path),
            'device': self.device,
            'feature_dim': self.feature_dim,
            'total_parameters': total_params,
            'trainable_parameters': trainable_params,
            'training_epochs': len(self.training_history),
            'model_exists': self.model_path.exists()
        }
