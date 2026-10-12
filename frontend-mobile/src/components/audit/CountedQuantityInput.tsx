import React from 'react';
import { View, Text, TextInput, StyleSheet, Platform } from 'react-native';
import { DeltaCalculator } from '../../services/domain/DeltaCalculator';
import { colors } from '../../utils/designTokens';

interface CountedQuantityInputProps {
  value: string;
  onChangeValue: (text: string) => void;
  stockBaseline: number;
}

export const CountedQuantityInput: React.FC<CountedQuantityInputProps> = ({
  value,
  onChangeValue,
  stockBaseline,
}) => {
  const numValue = value === '' ? stockBaseline : Number(value) || 0;
  const delta = DeltaCalculator.compute(stockBaseline, numValue);

  const getPillStyles = () => {
    switch (delta.actionType) {
      case 'Baja':
        return {
          pill: styles.pillBaja,
          dot: styles.dotBaja,
          text: styles.textBaja,
          label: 'Baja',
        };
      case 'Alta':
        return {
          pill: styles.pillAlta,
          dot: styles.dotAlta,
          text: styles.textAlta,
          label: 'Alta',
        };
      case 'Sin Acción':
      default:
        return {
          pill: styles.pillSinAccion,
          dot: styles.dotSinAccion,
          text: styles.textSinAccion,
          label: 'Sin Acción',
        };
    }
  };

  const pill = getPillStyles();

  const getDiscrepancyMessage = () => {
    if (value === '') return null;
    if (delta.actionType === 'Baja') {
      return `↓ Diferencia de ${delta.affectedQuantity} uds. respecto al sistema.`;
    }
    if (delta.actionType === 'Alta') {
      return `↑ Diferencia de +${delta.affectedQuantity} uds. respecto al sistema.`;
    }
    return '✓ Stock físico coincide con el sistema (0 uds. de diferencia).';
  };

  const msg = getDiscrepancyMessage();

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Cantidad contada</Text>

      {/* Input Box with Inline Action Pill */}
      <View style={styles.inputBox}>
        <TextInput
          style={styles.input}
          value={value}
          onChangeText={(t) => {
            // Only allow positive integers
            const cleaned = t.replace(/[^0-9]/g, '');
            onChangeValue(cleaned);
          }}
          placeholder={String(stockBaseline)}
          placeholderTextColor={colors.text.disabled}
          keyboardType="number-pad"
        />

        {/* Inline Action Pill */}
        <View style={[styles.inlinePill, pill.pill]}>
          <View style={[styles.dot, pill.dot]} />
          <Text style={[styles.pillText, pill.text]}>{pill.label}</Text>
        </View>
      </View>

      {/* Dynamic Discrepancy Tracker Message */}
      {msg && (
        <Text
          style={[
            styles.trackerMessage,
            delta.actionType === 'Baja'
              ? styles.trackerBaja
              : delta.actionType === 'Alta'
              ? styles.trackerAlta
              : styles.trackerSinAccion,
          ]}
        >
          {msg}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginBottom: 16,
  },
  label: {
    fontSize: 12,
    fontWeight: '600',
    color: colors.text.secondary,
    marginBottom: 6,
  },
  inputBox: {
    height: 48,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#CBD5E1',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
  },
  input: {
    flex: 1,
    fontSize: 18,
    fontWeight: '800',
    fontFamily: Platform.OS === 'ios' ? 'Courier' : 'monospace',
    color: colors.text.primary,
  },
  inlinePill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 9999,
  },
  dot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  pillText: {
    fontSize: 12,
    fontWeight: '700',
  },
  pillBaja: {
    backgroundColor: '#FEE2E2',
  },
  dotBaja: {
    backgroundColor: '#DC2626',
  },
  textBaja: {
    color: '#B91C1C',
  },
  pillAlta: {
    backgroundColor: '#D1FAE5',
  },
  dotAlta: {
    backgroundColor: '#059669',
  },
  textAlta: {
    color: '#047857',
  },
  pillSinAccion: {
    backgroundColor: '#F1F5F9',
  },
  dotSinAccion: {
    backgroundColor: '#64748B',
  },
  textSinAccion: {
    color: '#475569',
  },
  trackerMessage: {
    fontSize: 12,
    fontWeight: '500',
    marginTop: 6,
  },
  trackerBaja: {
    color: '#DC2626',
  },
  trackerAlta: {
    color: '#059669',
  },
  trackerSinAccion: {
    color: colors.text.muted,
  },
});
