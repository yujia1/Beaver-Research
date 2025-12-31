<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const props = defineProps({
  lot: {
    type: Object,
    required: true
  },
  ticker: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['close', 'submit'])

const formData = ref({
  purchaseDate: '',
  quantity: '',
  costPerShare: '',
  link: '',
  note: ''
})

// Initialize form with lot data
watch(() => props.lot, (newLot) => {
  if (newLot) {
    formData.value = {
      purchaseDate: newLot.purchaseDate,
      quantity: newLot.quantity.toString(),
      costPerShare: newLot.costPerShare.toString(),
      link: newLot.link || '',
      note: newLot.note || ''
    }
  }
}, { immediate: true })

const errors = ref({})

const validateForm = () => {
  errors.value = {}
  
  if (!formData.value.purchaseDate) {
    errors.value.purchaseDate = t('portfolio.errors.date_required')
  }
  
  if (!formData.value.quantity || formData.value.quantity <= 0) {
    errors.value.quantity = t('portfolio.errors.quantity_positive')
  }
  
  if (!formData.value.costPerShare || formData.value.costPerShare <= 0) {
    errors.value.costPerShare = t('portfolio.errors.cost_positive')
  }
  
  return Object.keys(errors.value).length === 0
}

const handleSubmit = () => {
  if (validateForm()) {
    emit('submit', {
      purchaseDate: formData.value.purchaseDate,
      quantity: parseInt(formData.value.quantity),
      costPerShare: parseFloat(formData.value.costPerShare),
      link: formData.value.link.trim(),
      note: formData.value.note.trim()
    })
  }
}

const handleClose = () => {
  emit('close')
}

const handleBackdropClick = (e) => {
  if (e.target === e.currentTarget) {
    handleClose()
  }
}
</script>

<template>
  <div class="modal-backdrop" @click="handleBackdropClick">
    <div class="modal-container">
      <div class="modal-header">
        <div>
          <h2 class="modal-title">{{ t('portfolio.modal.title_modify', { ticker: ticker }) }}</h2>
          <p class="modal-subtitle">{{ t('portfolio.modal.subtitle_modify') }}</p>
        </div>
        <button class="close-btn" @click="handleClose">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"></line>
            <line x1="6" y1="6" x2="18" y2="18"></line>
          </svg>
        </button>
      </div>

      <div class="modal-body">
        <form @submit.prevent="handleSubmit">
          <div class="form-row">
            <div class="form-group">
              <label for="quantity">{{ t('portfolio.modal.quantity') }}</label>
              <input
                id="quantity"
                v-model="formData.quantity"
                type="number"
                placeholder="0"
                class="form-input"
                :class="{ error: errors.quantity }"
                min="1"
                step="1"
              />
              <span v-if="errors.quantity" class="error-message">{{ errors.quantity }}</span>
            </div>

            <div class="form-group">
              <label for="purchaseDate">{{ t('portfolio.modal.purchase_calendar') }}</label>
              <input
                id="purchaseDate"
                v-model="formData.purchaseDate"
                type="date"
                class="form-input"
                :class="{ error: errors.purchaseDate }"
              />
              <span v-if="errors.purchaseDate" class="error-message">{{ errors.purchaseDate }}</span>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="costPerShare">{{ t('portfolio.modal.cost_per_share') }}</label>
              <input
                id="costPerShare"
                v-model="formData.costPerShare"
                type="number"
                placeholder="0.00"
                class="form-input"
                :class="{ error: errors.costPerShare }"
                min="0.01"
                step="0.01"
              />
              <span v-if="errors.costPerShare" class="error-message">{{ errors.costPerShare }}</span>
            </div>

            <div class="form-group">
              <label for="link">{{ t('portfolio.modal.link') }}</label>
              <input
                id="link"
                v-model="formData.link"
                type="url"
                placeholder="https://..."
                class="form-input"
              />
            </div>
          </div>

          <div class="form-group">
            <label for="note">{{ t('portfolio.modal.entry_notes') }}</label>
            <textarea
              id="note"
              v-model="formData.note"
              :placeholder="t('portfolio.modal.entry_notes_placeholder', 'Context for this purchase...')"
              class="form-textarea"
              rows="4"
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="submit" class="btn btn-submit">
              {{ t('portfolio.modal.update_lot') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  padding: 1rem;
}

.modal-container {
  background: #fff;
  border-radius: 12px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 2rem 2rem 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.5rem 0;
  color: #000;
  letter-spacing: 0.5px;
}

.modal-subtitle {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.5rem;
  color: #666;
  transition: color 0.2s;
  margin: -0.5rem -0.5rem 0 0;
}

.close-btn:hover {
  color: #000;
}

.modal-body {
  padding: 2rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #000;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.form-input,
.form-textarea {
  padding: 0.75rem 1rem;
  border: 1px solid #d0d0d0;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-family: inherit;
  transition: border-color 0.2s;
}

.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #000;
}

.form-input.error {
  border-color: #ef4444;
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #999;
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.error-message {
  font-size: 0.75rem;
  color: #ef4444;
  margin-top: -0.25rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.btn {
  flex: 1;
  padding: 0.875rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-size: 0.9375rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-submit {
  background: #000;
  color: #fff;
}

.btn-submit:hover {
  background: #333;
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }
  
  .modal-container {
    max-height: 95vh;
  }
  
  .modal-header,
  .modal-body {
    padding: 1.5rem;
  }
}
</style>
