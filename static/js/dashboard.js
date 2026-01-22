let configs = [];
let editingConfigId = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadConfigs();
    setupTabs();
    setupPurgeForm();
    setupConfigForm();
    
    // 清除类型变化时显示/隐藏目标输入框
    document.getElementById('purgeType').addEventListener('change', function() {
        const targetsGroup = document.getElementById('targetsGroup');
        if (this.value === 'purge_all') {
            targetsGroup.style.display = 'none';
        } else {
            targetsGroup.style.display = 'block';
        }
    });
});

// 标签页切换
function setupTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            // 更新按钮状态
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            // 更新内容显示
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            document.getElementById(tabName + 'Tab').classList.add('active');
            
            // 如果切换到清除标签页，重新加载配置列表
            if (tabName === 'purge') {
                loadConfigsForPurge();
            }
        });
    });
}

// 加载配置列表
async function loadConfigs() {
    try {
        const response = await fetch('/api/configs');
        configs = await response.json();
        renderConfigTable();
    } catch (error) {
        console.error('Load configs error:', error);
    }
}

// 渲染配置表格
function renderConfigTable() {
    const tbody = document.getElementById('configTableBody');
    
    if (configs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center">暂无配置，请添加</td></tr>';
        return;
    }
    
    tbody.innerHTML = configs.map(config => `
        <tr>
            <td>${config.name || '未命名'}</td>
            <td>${config.secret_id}</td>
            <td>${config.zone_id}</td>
            <td>${config.region === 'cn' ? '国内版' : '国际版'}</td>
            <td>${new Date(config.updated_at).toLocaleString('zh-CN')}</td>
            <td>
                <button class="btn btn-primary btn-sm" onclick="editConfig(${config.id})">编辑</button>
                <button class="btn btn-danger btn-sm" onclick="deleteConfig(${config.id})">删除</button>
            </td>
        </tr>
    `).join('');
}

// 加载配置到清除表单
async function loadConfigsForPurge() {
    try {
        const response = await fetch('/api/configs');
        const configs = await response.json();
        const select = document.getElementById('purgeConfig');
        
        select.innerHTML = '<option value="">请选择配置</option>' +
            configs.map(config => 
                `<option value="${config.id}">${config.name || '未命名'} (${config.zone_id})</option>`
            ).join('');
    } catch (error) {
        console.error('Load configs for purge error:', error);
    }
}

// 显示添加配置模态框
function showAddConfigModal() {
    editingConfigId = null;
    document.getElementById('modalTitle').textContent = '添加配置';
    document.getElementById('configForm').reset();
    document.getElementById('configId').value = '';
    document.getElementById('configModal').style.display = 'block';
}

// 编辑配置
async function editConfig(id) {
    try {
        const response = await fetch(`/api/configs/${id}`);
        const config = await response.json();
        
        editingConfigId = id;
        document.getElementById('modalTitle').textContent = '编辑配置';
        document.getElementById('configId').value = config.id;
        document.getElementById('configName').value = config.name || '';
        document.getElementById('secretId').value = config.secret_id;
        document.getElementById('secretKey').value = config.secret_key;
        document.getElementById('zoneId').value = config.zone_id;
        document.getElementById('region').value = config.region;
        document.getElementById('configModal').style.display = 'block';
    } catch (error) {
        alert('加载配置失败: ' + error.message);
        console.error('Edit config error:', error);
    }
}

// 关闭配置模态框
function closeConfigModal() {
    document.getElementById('configModal').style.display = 'none';
    editingConfigId = null;
}

// 设置配置表单
function setupConfigForm() {
    document.getElementById('configForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('configName').value,
            secret_id: document.getElementById('secretId').value,
            secret_key: document.getElementById('secretKey').value,
            zone_id: document.getElementById('zoneId').value,
            region: document.getElementById('region').value
        };
        
        const configId = document.getElementById('configId').value;
        const url = configId ? `/api/configs/${configId}` : '/api/configs';
        const method = configId ? 'PUT' : 'POST';
        
        try {
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                closeConfigModal();
                loadConfigs();
                if (method === 'POST') {
                    loadConfigsForPurge();
                }
            } else {
                alert('保存失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            alert('保存失败: ' + error.message);
            console.error('Save config error:', error);
        }
    });
}

// 删除配置
async function deleteConfig(id) {
    if (!confirm('确定要删除这个配置吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/configs/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadConfigs();
            loadConfigsForPurge();
        } else {
            alert('删除失败: ' + (data.message || '未知错误'));
        }
    } catch (error) {
        alert('删除失败: ' + error.message);
        console.error('Delete config error:', error);
    }
}

// 设置清除表单
function setupPurgeForm() {
    document.getElementById('purgeForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const resultDiv = document.getElementById('purgeResult');
        resultDiv.className = 'result-message';
        resultDiv.textContent = '提交中...';
        
        const formData = {
            config_id: parseInt(document.getElementById('purgeConfig').value),
            type: document.getElementById('purgeType').value,
            method: document.getElementById('purgeMethod').value,
            targets: []
        };
        
        const targetsInput = document.getElementById('targets').value.trim();
        if (targetsInput && formData.type !== 'purge_all') {
            formData.targets = targetsInput.split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
        }
        
        try {
            const response = await fetch('/api/purge', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                resultDiv.className = 'result-message success';
                resultDiv.textContent = '✓ ' + (data.message || '缓存清除任务已提交');
                document.getElementById('purgeForm').reset();
                document.getElementById('targetsGroup').style.display = 'none';
            } else {
                resultDiv.className = 'result-message error';
                resultDiv.textContent = '✗ ' + (data.message || '提交失败');
            }
        } catch (error) {
            resultDiv.className = 'result-message error';
            resultDiv.textContent = '✗ 网络错误: ' + error.message;
            console.error('Purge error:', error);
        }
    });
}

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('configModal');
    if (event.target === modal) {
        closeConfigModal();
    }
}
