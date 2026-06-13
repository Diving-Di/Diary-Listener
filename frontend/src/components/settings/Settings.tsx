import { useEffect, useState } from 'react'
import { Button, Card, Spin, Switch, message as antdMessage } from 'antd'
import { fetchSettings, updateSettings } from '../../api/settings'
import { reindexDiary } from '../../api/diary'
import './Settings.css'

interface SettingsProps {
  token: string
}

export default function Settings({ token }: SettingsProps) {
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const [allowAiDiary, setAllowAiDiary] = useState(true)

  useEffect(() => {
    loadSettings()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function loadSettings() {
    setLoading(true)
    try {
      const data = await fetchSettings(token)
      setAllowAiDiary(data.allow_ai_diary)
    } catch (e) {
      antdMessage.error('加载设置失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleToggle(checked: boolean) {
    setSaving(true)
    setAllowAiDiary(checked)
    try {
      await updateSettings(token, { allow_ai_diary: checked })
      antdMessage.success('已保存')
    } catch (e) {
      antdMessage.error('保存失败')
      setAllowAiDiary(!checked)
    } finally {
      setSaving(false)
    }
  }

  async function handleReindex() {
    setReindexing(true)
    try {
      const r = await reindexDiary(token)
      antdMessage.success(
        `重建完成：扫描 ${r.processed} 条，新增配图描述 ${r.captioned} 条，更新向量 ${r.embedded} 条`,
      )
    } catch (e) {
      antdMessage.error('重建失败')
    } finally {
      setReindexing(false)
    }
  }

  return (
    <div className="settings">
      <Card className="settings-card" title="设置">
        {loading ? (
          <div className="settings-loading">
            <Spin />
          </div>
        ) : (
          <>
            <div className="settings-item">
              <div className="settings-item-text">
                <div className="settings-item-title">允许 AI 参考我的日记</div>
                <div className="settings-item-desc">
                  开启后，聊天时 AI 会参考你日记中的心情、经历与情绪，给出更懂你的回复。
                  你的日记仅用于此目的，可随时关闭。
                </div>
              </div>
              <Switch checked={allowAiDiary} loading={saving} onChange={handleToggle} />
            </div>
            <div className="settings-item">
              <div className="settings-item-text">
                <div className="settings-item-title">重建日记记忆</div>
                <div className="settings-item-desc">
                  为已有日记补全配图的文字描述并重新建立语义索引。
                  通常在首次开启或更换模型后使用一次即可。
                </div>
              </div>
              <Button loading={reindexing} onClick={handleReindex}>
                重建
              </Button>
            </div>
          </>
        )}
      </Card>
    </div>
  )
}
