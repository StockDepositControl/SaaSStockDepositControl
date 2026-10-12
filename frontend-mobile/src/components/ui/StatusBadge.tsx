import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { ArticleAuditStatus } from '../../types/article';

interface StatusBadgeProps {
  status: ArticleAuditStatus;
  variant?: 'prominent' | 'neutral';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant = 'prominent',
}) => {
  const isAudited = status === 'audited';

  const containerStyle = isAudited
    ? styles.auditedContainer
    : variant === 'neutral'
    ? styles.pendingNeutralContainer
    : styles.pendingContainer;

  const textStyle = isAudited
    ? styles.auditedText
    : variant === 'neutral'
    ? styles.pendingNeutralText
    : styles.pendingText;

  return (
    <View style={[styles.badge, containerStyle]}>
      <Text style={[styles.badgeText, textStyle]}>
        {isAudited ? 'AUDITADO' : 'PENDIENTE'}
      </Text>
    </View>
  );
};

const styles = StyleSheet.create({
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 9999,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  auditedContainer: {
    backgroundColor: '#D1FAE5',
  },
  auditedText: {
    color: '#047857',
  },
  pendingContainer: {
    backgroundColor: '#FEF3C7',
  },
  pendingText: {
    color: '#B45309',
  },
  pendingNeutralContainer: {
    backgroundColor: '#F1F5F9',
  },
  pendingNeutralText: {
    color: '#64748B',
  },
});
