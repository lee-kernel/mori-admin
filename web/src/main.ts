import { createApp } from 'vue'
import RootApp from '@/App.vue'
import router from '@/router'
import { createPinia } from 'pinia'
import Alert from 'ant-design-vue/es/alert'
import AntApp from 'ant-design-vue/es/app'
import AutoComplete from 'ant-design-vue/es/auto-complete'
import Avatar from 'ant-design-vue/es/avatar'
import Badge from 'ant-design-vue/es/badge'
import Button from 'ant-design-vue/es/button'
import Card from 'ant-design-vue/es/card'
import Cascader from 'ant-design-vue/es/cascader'
import Checkbox from 'ant-design-vue/es/checkbox'
import Collapse from 'ant-design-vue/es/collapse'
import ConfigProvider from 'ant-design-vue/es/config-provider'
import DatePicker from 'ant-design-vue/es/date-picker'
import Descriptions from 'ant-design-vue/es/descriptions'
import Divider from 'ant-design-vue/es/divider'
import Drawer from 'ant-design-vue/es/drawer'
import Dropdown from 'ant-design-vue/es/dropdown'
import Empty from 'ant-design-vue/es/empty'
import Form from 'ant-design-vue/es/form'
import Input from 'ant-design-vue/es/input'
import InputNumber from 'ant-design-vue/es/input-number'
import List from 'ant-design-vue/es/list'
import Menu from 'ant-design-vue/es/menu'
import Modal from 'ant-design-vue/es/modal'
import Pagination from 'ant-design-vue/es/pagination'
import Popconfirm from 'ant-design-vue/es/popconfirm'
import Popover from 'ant-design-vue/es/popover'
import QRCode from 'ant-design-vue/es/qrcode'
import Result from 'ant-design-vue/es/result'
import Radio from 'ant-design-vue/es/radio'
import Segmented from 'ant-design-vue/es/segmented'
import Select from 'ant-design-vue/es/select'
import Space from 'ant-design-vue/es/space'
import Spin from 'ant-design-vue/es/spin'
import Switch from 'ant-design-vue/es/switch'
import Table from 'ant-design-vue/es/table'
import Tabs from 'ant-design-vue/es/tabs'
import Tag from 'ant-design-vue/es/tag'
import TimePicker from 'ant-design-vue/es/time-picker'
import Tooltip from 'ant-design-vue/es/tooltip'
import Tree from 'ant-design-vue/es/tree'
import TreeSelect from 'ant-design-vue/es/tree-select'
import Typography from 'ant-design-vue/es/typography'
import Upload from 'ant-design-vue/es/upload'

// 引入全局默认样式
import 'ant-design-vue/dist/reset.css'
import '@/styles/index.scss'

// 仅注册模板中实际使用的组件，避免全量 Ant Design Vue 进入首屏包。
const antdComponents = [
  Alert,
  AntApp,
  AutoComplete,
  Avatar,
  Badge,
  Button,
  Card,
  Cascader,
  Checkbox,
  Collapse,
  ConfigProvider,
  DatePicker,
  Descriptions,
  Divider,
  Drawer,
  Dropdown,
  Empty,
  Form,
  Input,
  InputNumber,
  List,
  Menu,
  Modal,
  Pagination,
  Popconfirm,
  Popover,
  QRCode,
  Radio,
  Result,
  Segmented,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tabs,
  Tag,
  TimePicker,
  Tooltip,
  Tree,
  TreeSelect,
  Typography,
  Upload,
]

const app = createApp(RootApp)
const pinia = createPinia()

antdComponents.forEach((component) => app.use(component))
app.use(pinia)
app.use(router)

app.mount('#app')
