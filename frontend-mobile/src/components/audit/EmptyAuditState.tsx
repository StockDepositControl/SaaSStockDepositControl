import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Icon } from '../ui/Icon';
import { colors } from '../../utils/designTokens';

interface EmptyAuditStateProps {
  errorMessage?: string | null;
}

export const EmptyAuditState: React.FC<EmptyAuditStateProps> = ({ errorMessage }) => {
  return (
    <View style={styles.container}>
      {errorMessage ? (
        <View style={styles.errorCard}>
          <Icon name="alert-circle" size={20} color="#DC2626" />
          <Text style={styles.errorText}>{errorMessage}</Text>
        </View>
      ) : null}

      <View style={styles.content}>
        <View style={styles.iconCircle}>
          <Icon name="search" size={28} color="#94A3B8" />
        </View>
        <Text style={styles.titleText}>Buscá o escaneá un artículo para auditar</Text>
        <Text style={styles.subtitleText}>
          Ingresá el código de barras (EAN), código interno o nombre del producto, o usá el botón de cámara.
        </Text>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 16,
  },
  errorCard: {
    backgroundColor: '#FEF2F2',
    borderWidth: 1,
    borderColor: '#FECACA',
    borderRadius: 12,
    padding: 14,
    marginTop: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  errorText: {
    flex: 1,
    fontSize: 12,
    fontWeight: '600',
    color: '#B91C1C',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
    paddingBottom: 48,
  },
  iconCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#F1F5F9',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  titleText: {
    fontSize: 15,
    fontWeight: '700',
    color: colors.text.secondary,
    textAlign: 'center',
    marginBottom: 6,
  },
  subtitleText: {
    fontSize: 12,
    color: colors.text.disabled,
    textAlign: 'center',
    lineHeight: 18,
  },
});
