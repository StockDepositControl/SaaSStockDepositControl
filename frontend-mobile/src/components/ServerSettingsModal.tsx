import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ActivityIndicator,
  Modal,
  StyleSheet,
} from 'react-native';
import { colors } from '../utils/designTokens';
import {
  checkServerHealth,
  getServerUrl,
  normalizeServerUrl,
  setServerUrl,
} from '../utils/serverUrl';

interface ServerSettingsModalProps {
  visible: boolean;
  onClose: () => void;
}

type TestStatus = 'idle' | 'testing' | 'ok' | 'error';

export const ServerSettingsModal: React.FC<ServerSettingsModalProps> = ({ visible, onClose }) => {
  const [url, setUrl] = useState('');
  const [status, setStatus] = useState<TestStatus>('idle');
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    if (!visible) return;
    setStatus('idle');
    setSaveError(null);
    getServerUrl().then(setUrl);
  }, [visible]);

  const handleTest = async () => {
    setStatus('testing');
    setSaveError(null);
    setStatus((await checkServerHealth(url)) ? 'ok' : 'error');
  };

  const handleSave = async () => {
    try {
      await setServerUrl(url);
      onClose();
    } catch (e) {
      setSaveError(e instanceof Error ? e.message : 'No se pudo guardar la URL.');
    }
  };

  const canSave = status === 'ok' && normalizeServerUrl(url) !== null;

  return (
    <Modal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <Text style={styles.title}>Configuración del Servidor</Text>
          <Text style={styles.label}>URL del servidor</Text>
          <TextInput
            style={styles.input}
            value={url}
            onChangeText={(val) => {
              setUrl(val);
              setStatus('idle');
              setSaveError(null);
            }}
            placeholder="https://stock.tu-dominio.com"
            placeholderTextColor={colors.text.disabled}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
          />

          {status === 'ok' && <Text style={styles.statusOk}>Conexión exitosa.</Text>}
          {status === 'error' && (
            <Text style={styles.statusError}>No se pudo conectar con el servidor.</Text>
          )}
          {saveError && <Text style={styles.statusError}>{saveError}</Text>}

          <Pressable
            onPress={handleTest}
            disabled={status === 'testing'}
            style={[styles.button, styles.secondaryButton]}
          >
            {status === 'testing' ? (
              <ActivityIndicator color={colors.primary[500]} size="small" />
            ) : (
              <Text style={styles.secondaryButtonText}>Probar Conexión</Text>
            )}
          </Pressable>

          <View style={styles.actions}>
            <Pressable onPress={onClose} style={[styles.button, styles.cancelButton]}>
              <Text style={styles.secondaryButtonText}>Cancelar</Text>
            </Pressable>
            <Pressable
              onPress={handleSave}
              disabled={!canSave}
              style={[styles.button, styles.saveButton, !canSave && styles.saveButtonDisabled]}
            >
              <Text style={styles.saveButtonText}>Guardar</Text>
            </Pressable>
          </View>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  sheet: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    padding: 20,
  },
  title: {
    fontSize: 16,
    fontWeight: '800',
    color: colors.text.primary,
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.primary,
    marginBottom: 6,
  },
  input: {
    height: 48,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 14,
    fontSize: 14,
    color: colors.text.primary,
    marginBottom: 12,
  },
  statusOk: {
    fontSize: 12,
    fontWeight: '600',
    color: '#15803D',
    marginBottom: 12,
  },
  statusError: {
    fontSize: 12,
    fontWeight: '600',
    color: '#B91C1C',
    marginBottom: 12,
  },
  button: {
    height: 44,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  secondaryButton: {
    borderWidth: 1,
    borderColor: colors.primary[500],
    marginBottom: 16,
  },
  secondaryButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: colors.primary[500],
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  cancelButton: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  saveButton: {
    flex: 1,
    backgroundColor: colors.primary[500],
  },
  saveButtonDisabled: {
    backgroundColor: colors.text.disabled,
  },
  saveButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
});
