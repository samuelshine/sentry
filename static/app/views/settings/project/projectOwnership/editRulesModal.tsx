import {Fragment} from 'react';
import styled from '@emotion/styled';

import {EditOwnershipRulesModalOptions} from 'sentry/actionCreators/modal';
import {t} from 'sentry/locale';
import TextBlock from 'sentry/views/settings/components/text/textBlock';
import OwnerInput from 'sentry/views/settings/project/projectOwnership/ownerInput';

interface EditOwnershipRulesModalProps extends EditOwnershipRulesModalOptions {
  onCancel: () => void;
}

function EditOwnershipRulesModal(props: EditOwnershipRulesModalProps) {
  const {ownership} = props;
  return (
    <Fragment>
      <Block>
        {t('Globbing Syntax')}
        <CodeBlock>{'* matches everything\n? matches any single character'}</CodeBlock>
      </Block>
      <Block>
        {t('Examples')}
        <CodeBlock>
          path:src/example/pipeline/* person@sentry.io #infra
          {'\n'}
          module:com.module.name.example #sdks
          {'\n'}
          url:http://example.com/settings/* #product #infra
          {'\n'}
          tags.sku_class:enterprise #enterprise
        </CodeBlock>
      </Block>
      {ownership && <OwnerInput {...props} initialText={ownership.raw || ''} />}
    </Fragment>
  );
}

const Block = styled(TextBlock)`
  margin-bottom: 16px;
`;

const CodeBlock = styled('pre')`
  word-break: break-all;
  white-space: pre-wrap;
`;

export default EditOwnershipRulesModal;
