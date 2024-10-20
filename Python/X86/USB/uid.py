from smartcard.scard import (
    SCardGetErrorMessage,
    SCARD_SCOPE_USER,
    SCARD_S_SUCCESS,
    SCARD_SHARE_SHARED,
    SCARD_PROTOCOL_T0,
    SCARD_PROTOCOL_T1,
    SCARD_CTL_CODE,
    SCardEstablishContext,
    SCardListReaders,
    SCardConnect,
    SCardControl

)
from smartcard.System import readers
from smartcard.Exceptions import NoCardException
import time
while True:
    time.sleep(1)

    try:
        hresult, hcontext = SCardEstablishContext(SCARD_SCOPE_USER)
        print('test')
        if hresult == SCARD_S_SUCCESS:
            print('next')
            hresult, readers = SCardListReaders(hcontext, [])
            if len(readers) > 0:
                print('supernext')
                reader = readers[0]
                hresult, hcard, dwActiveProtocol = SCardConnect(hcontext, reader, SCARD_SHARE_SHARED, SCARD_PROTOCOL_T0 | SCARD_PROTOCOL_T1)

                apdu_cmd = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                if hcard>0:
                    hresult, response = SCardControl(hcard, SCARD_CTL_CODE(3500), apdu_cmd)
                    if hresult != SCARD_S_SUCCESS:
                        print(SCardGetErrorMessage(hresult))

                    print('NFC tag UID is:', ''.join(map(lambda x: f'{x:02x}', response[:-2])).replace('0x', ''))
                    test = nfc = ''.join(map(lambda x: f'{x:02x}', response[:-2])).replace('0x', '')
                    print(test)
    except NoCardException:
        print(reader, 'no card inserted')   