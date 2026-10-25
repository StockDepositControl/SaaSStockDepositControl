import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  Pressable,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StyleSheet,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { Icon } from '../components/ui/Icon';
import { colors } from '../utils/designTokens';
import { ServerSettingsModal } from '../components/ServerSettingsModal';

export const LoginScreen: React.FC = () => {
  const { login, isLoading, loginError, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const [showServerSettings, setShowServerSettings] = useState(false);

  const handleLogin = async () => {
    setValidationError(null);
    clearError();

    const cleanEmail = email.trim();
    if (!cleanEmail) {
      setValidationError('Ingresá tu correo electrónico.');
      return;
    }
    if (!password) {
      setValidationError('Ingresá tu contraseña.');
      return;
    }

    try {
      await login({ email: cleanEmail, password });
    } catch {
      // Error handled via AuthContext loginError
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        keyboardShouldPersistTaps="handled"
      >
        {/* Brand Identity Header */}
        <View style={styles.brandContainer}>
          <View style={styles.brandIconBadge}>
            <Icon name="clipboard-check" size={26} color={colors.primary[500]} />
          </View>
          <Text style={styles.brandTitle}>Audit Global</Text>
          <Text style={styles.brandSubtitle}>Sistema de control e inventario</Text>
        </View>

        {/* Authentication Card */}
        <View style={styles.card}>
          {/* Top Blue Accent Bar */}
          <View style={styles.topAccentBar} />

          <View style={styles.cardBody}>
            {/* Error Banner */}
            {(loginError || validationError) && (
              <View style={styles.errorBanner}>
                <Icon name="alert-circle" size={18} color="#DC2626" />
                <Text style={styles.errorText}>
                  {validationError || loginError}
                </Text>
              </View>
            )}

            {/* Email Field */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Correo electrónico</Text>
              <TextInput
                style={styles.input}
                value={email}
                onChangeText={(val) => {
                  setEmail(val);
                  setValidationError(null);
                  clearError();
                }}
                placeholder="usuario@globalmedica.com"
                placeholderTextColor={colors.text.disabled}
                autoCapitalize="none"
                keyboardType="email-address"
                autoCorrect={false}
              />
            </View>

            {/* Password Field */}
            <View style={styles.inputGroup}>
              <Text style={styles.inputLabel}>Contraseña</Text>
              <View style={styles.passwordWrapper}>
                <TextInput
                  style={styles.passwordInput}
                  value={password}
                  onChangeText={(val) => {
                    setPassword(val);
                    setValidationError(null);
                    clearError();
                  }}
                  placeholder="••••••••"
                  placeholderTextColor={colors.text.disabled}
                  secureTextEntry={!showPassword}
                  autoCapitalize="none"
                />
                <Pressable
                  onPress={() => setShowPassword(!showPassword)}
                  style={styles.eyeButton}
                  hitSlop={8}
                >
                  <Icon
                    name={showPassword ? 'eye-off' : 'eye'}
                    size={18}
                    color={colors.text.muted}
                  />
                </Pressable>
              </View>
            </View>

            {/* Primary Action Button */}
            <Pressable
              onPress={handleLogin}
              disabled={isLoading}
              style={({ pressed }) => [
                styles.submitButton,
                pressed && styles.submitButtonPressed,
                isLoading && styles.submitButtonDisabled,
              ]}
            >
              {isLoading ? (
                <ActivityIndicator color="#FFFFFF" size="small" />
              ) : (
                <Text style={styles.submitButtonText}>Ingresar</Text>
              )}
            </Pressable>
          </View>

          {/* Role Restriction Notice Footer */}
          <View style={styles.cardFooter}>
            <Text style={styles.cardFooterText}>
              El acceso es restringido por rol. Contactá a tu administrador si no podés ingresar.
            </Text>
          </View>
        </View>

        <Pressable
          onPress={() => setShowServerSettings(true)}
          style={styles.serverLink}
          hitSlop={8}
        >
          <Text style={styles.serverLinkText}>Configuración del Servidor</Text>
        </Pressable>
      </ScrollView>

      <ServerSettingsModal
        visible={showServerSettings}
        onClose={() => setShowServerSettings(false)}
      />
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background.base,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: 20,
    paddingVertical: 32,
  },
  brandContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  brandIconBadge: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primary[50],
    borderWidth: 1,
    borderColor: colors.primary[200],
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 14,
  },
  brandTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: colors.text.primary,
    letterSpacing: -0.5,
    textAlign: 'center',
  },
  brandSubtitle: {
    fontSize: 13,
    fontWeight: '500',
    color: colors.text.muted,
    marginTop: 4,
    textAlign: 'center',
  },
  card: {
    backgroundColor: colors.background.surface,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: colors.background.surfaceMuted,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  topAccentBar: {
    height: 6,
    width: '100%',
    backgroundColor: colors.primary[500],
  },
  cardBody: {
    padding: 20,
  },
  errorBanner: {
    backgroundColor: '#FEF2F2',
    borderColor: '#FECACA',
    borderWidth: 1,
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  errorText: {
    fontSize: 12,
    color: '#B91C1C',
    fontWeight: '500',
    flex: 1,
  },
  inputGroup: {
    marginBottom: 16,
  },
  inputLabel: {
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
  },
  passwordWrapper: {
    height: 48,
    borderRadius: 10,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#CBD5E1',
    paddingHorizontal: 14,
    flexDirection: 'row',
    alignItems: 'center',
  },
  passwordInput: {
    flex: 1,
    fontSize: 14,
    color: colors.text.primary,
  },
  eyeButton: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  submitButton: {
    height: 48,
    borderRadius: 10,
    backgroundColor: colors.primary[500],
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 8,
  },
  submitButtonPressed: {
    backgroundColor: colors.primary[600],
  },
  submitButtonDisabled: {
    backgroundColor: colors.text.disabled,
  },
  submitButtonText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#FFFFFF',
  },
  cardFooter: {
    backgroundColor: colors.background.base,
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
    paddingHorizontal: 16,
    paddingVertical: 14,
  },
  serverLink: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    marginTop: 20,
  },
  serverLinkText: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.muted,
  },
  cardFooterText: {
    fontSize: 11,
    lineHeight: 16,
    color: colors.text.muted,
    textAlign: 'center',
  },
});
